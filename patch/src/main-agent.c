/**
 * \file main-agent.c
 * \brief A frontend that hands the screen to an agent and takes keys back.
 *
 * This is the whole of borg-runner's harness, and it is deliberately stupid:
 * when the game asks for input and our key buffer is empty, it writes the
 * screen as the game drew it and waits for a file holding the keys to press.
 * It parses nothing, decides nothing and remembers nothing on the agent's
 * behalf (docs/DESIGN.md, D2-D4).
 *
 * It is a *frontend*, so the game's own code is untouched: the only upstream
 * files the patch edits are the build file, main.c and main.h, and all three
 * only to register this one.
 */
#include "angband.h"
#include "game-world.h"
#include "obj-power.h"
#include "init.h"
#include "ui-command.h"
#include "ui-display.h"
#include "ui-game.h"
#include "ui-input.h"
#include "ui-output.h"
#include "ui-term.h"
#include "main.h"
#include "z-rand.h"

#include <errno.h>
#include <sys/stat.h>
#include <time.h>
#include <unistd.h>

#ifdef USE_AGENT

#define AGENT_KEYS 1024

static term agent_term;
static char agent_directory[1024] = ".";
static uint32_t agent_seed;
static bool agent_seeded;

/* The keys still to press, and where we are in them.
 *
 * Keycodes, not bytes: Angband's Enter is KC_ENTER (0x9c), not carriage
 * return, and a prompt that says "Press Return" will not take 0x0d. Found by
 * saving the game and watching it sit there. */
static keycode_t agent_buffer[AGENT_KEYS];
static size_t agent_at;
static size_t agent_held;

/* How many times we have asked. The files are numbered by the ask, so a
 * question and its answer always pair up even when the game asks twice
 * without anything having changed. */
static long agent_asks;

/* Where the game last put the cursor. A person sees a menu's highlight as
 * reverse video; our screen is characters only, so without this the agent
 * cannot tell which item is selected - and Angband's birth menus move the
 * highlight on a letter and select on Enter. Found by playing it. */
static int agent_cursor_x;
static int agent_cursor_y;

static void agent_path(char *out, size_t size, const char *what, long number)
{
    strnfmt(out, size, "%s/%s-%ld.txt", agent_directory, what, number);
}

/**
 * The screen, exactly as the game drew it: 80 columns, 24 rows, no
 * interpretation. Trailing blanks are dropped so the file stays readable;
 * nothing else is touched.
 */
static void agent_write_screen(const char *path)
{
    ang_file *file = file_open(path, MODE_WRITE, FTYPE_TEXT);
    int y, x, width, height;

    if (!file)
        quit_fmt("agent: cannot write %s", path);

    Term_get_size(&width, &height);
    for (y = 0; y < height; y++) {
        char line[256];
        int end = 0;
        for (x = 0; x < width && x < (int)sizeof(line) - 1; x++) {
            int attribute;
            wchar_t character;
            if (Term_what(x, y, &attribute, &character) != 0)
                character = L' ';
            /* The map is drawn with wide characters; the ones Angband uses
             * are all representable, and anything else becomes a space
             * rather than a broken byte sequence. */
            line[x] = (character > 0 && character < 128) ? (char)character : ' ';
            if (line[x] != ' ')
                end = x + 1;
        }
        line[end] = '\0';
        file_putf(file, "%s\n", line);
    }
    file_close(file);
}

/**
 * Wait for the answer file and take the keys out of it.
 *
 * The file is plain text: every byte in it is a key to press, except that a
 * trailing newline is dropped and the two-character escapes stand for keys
 * that cannot be typed into a file:
 *
 *   \n  Enter   (KC_ENTER, which is what the game's prompts wait for)
 *   \e  Escape
 *   \t  Tab
 *   \\  a literal backslash
 */
static bool agent_read_keys(const char *path)
{
    ang_file *file;
    char raw[AGENT_KEYS];
    size_t read = 0, i;

    /* No timeout here on purpose: the agent's thinking time is not the
     * game's business, and a run that waits is better than a run that
     * invents a key. The runner outside imposes the limits. */
    while (!file_exists(path))
        usleep(100000);

    file = file_open(path, MODE_READ, FTYPE_TEXT);
    if (!file)
        return false;
    read = file_read(file, raw, sizeof(raw) - 1);
    file_close(file);
    if (read == (size_t)-1)
        read = 0;

    agent_at = agent_held = 0;
    for (i = 0; i < read && agent_held < N_ELEMENTS(agent_buffer); i++) {
        if (raw[i] == '\\' && i + 1 < read) {
            switch (raw[i + 1]) {
            case 'n': agent_buffer[agent_held++] = KC_ENTER; i++; continue;
            case 'e': agent_buffer[agent_held++] = ESCAPE; i++; continue;
            case 't': agent_buffer[agent_held++] = KC_TAB; i++; continue;
            case '\\': agent_buffer[agent_held++] = '\\'; i++; continue;
            default: break;
            }
        }
        if (raw[i] == '\n' && i + 1 == read)
            continue;           /* the newline a text editor adds, not a key */
        if (raw[i] == '\r' || raw[i] == '\n')
            agent_buffer[agent_held++] = KC_ENTER;
        else
            agent_buffer[agent_held++] = (keycode_t)(unsigned char)raw[i];
    }
    return agent_held > 0;
}

/**
 * What the character is worth carrying, by the game's own valuation.
 *
 * `object_value()` is what the game itself uses, so this is not an estimate
 * of ours: the pack, the quiver and what is worn, each at its own quantity.
 * Reported because depth alone does not say how a character was doing - a
 * level 6 pauper and a level 6 character with escapes are different runs.
 */
static int32_t agent_carried_value(void)
{
    struct object *obj;
    int32_t worth = 0;

    if (!player)
        return 0;
    for (obj = player->gear; obj; obj = obj->next)
        worth += object_value(obj, obj->number);
    return worth;
}


/**
 * The game wants input. If we are part way through a key string, press the
 * next one; otherwise show the screen and ask.
 *
 * Feeding a string from a buffer is what makes a multi-key command - throw,
 * then an item letter, then a target - cost one round trip rather than three
 * (D3), and what lets the agent use the game's own multi-turn commands (D5).
 */
static errr agent_event(int wait)
{
    char screen[1024], question[1024], answer[1024];

    if (agent_at < agent_held) {
        Term_keypress(agent_buffer[agent_at++], 0);
        return 0;
    }

    if (!wait)
        return 1;

    agent_asks++;
    agent_path(screen, sizeof(screen), "screen", agent_asks);
    agent_path(question, sizeof(question), "question", agent_asks);
    agent_path(answer, sizeof(answer), "keys", agent_asks);

    agent_write_screen(screen);
    /* The question is the screen's path and the turn; everything the agent
     * needs to know is on the screen itself. */
    {
        ang_file *file = file_open(question, MODE_WRITE, FTYPE_TEXT);
        if (file) {
            file_putf(file, "ask %ld\n", agent_asks);
            file_putf(file, "turn %d\n", (int)turn);
            /* turn++ happens in the outer game loop, so it lags through a
             * burst of prompts: -more-, a level feeling, a menu. Depth is the
             * honest progress signal, and it is the number this project is
             * about. Both are the game's own counters, not a reading of the
             * screen. */
            file_putf(file, "depth %d\n", player ? (int)player->depth : -1);
            file_putf(file, "max_depth %d\n", player ? (int)player->max_depth : -1);
            file_putf(file, "level %d\n", player ? (int)player->lev : -1);
            file_putf(file, "hp %d %d\n", player ? (int)player->chp : -1,
                      player ? (int)player->mhp : -1);
            file_putf(file, "gold %d\n", player ? (int)player->au : -1);
            file_putf(file, "carried %d\n", (int)agent_carried_value());
            /* Who is playing. The run asks for a random race and class, so
             * nothing but the game knows which were drawn, and a run whose
             * knowledge turns out to be one class's knowledge can only be
             * spotted if the record says the class. */
            file_putf(file, "race %s\n",
                      (player && player->race) ? player->race->name : "?");
            file_putf(file, "class %s\n",
                      (player && player->class) ? player->class->name : "?");
            file_putf(file, "cursor %d %d\n", agent_cursor_x, agent_cursor_y);
            file_putf(file, "screen %s\n", screen);
            file_putf(file, "answer_to %s\n", answer);
            file_close(file);
        }
    }

    if (!agent_read_keys(answer))
        return 1;
    if (agent_at < agent_held)
        Term_keypress(agent_buffer[agent_at++], 0);
    return 0;
}

static errr agent_xtra(int n, int v)
{
    switch (n) {
    case TERM_XTRA_EVENT:
        return agent_event(v);
    case TERM_XTRA_FLUSH:
        /* The game flushes input after a disturbance. Our buffer is the
         * agent's intent, and dropping it silently would make a key
         * disappear without record, so we keep it and let the agent see
         * what happened on the next screen. */
        return 0;
    case TERM_XTRA_CLEAR:
    case TERM_XTRA_FRESH:
    case TERM_XTRA_SHAPE:
    case TERM_XTRA_NOISE:
    case TERM_XTRA_DELAY:
    case TERM_XTRA_REACT:
        return 0;
    default:
        return 1;
    }
}

static errr agent_curs(int x, int y)
{
    agent_cursor_x = x;
    agent_cursor_y = y;
    return 0;
}
static errr agent_wipe(int x, int y, int n) { return 0; }
static errr agent_text(int x, int y, int n, int a, const wchar_t *s) { return 0; }

static void agent_term_link(int i)
{
    term *t = &agent_term;

    term_init(t, 80, 24, 256);
    t->xtra_hook = agent_xtra;
    t->curs_hook = agent_curs;
    t->wipe_hook = agent_wipe;
    t->text_hook = agent_text;
    Term_activate(t);
    angband_term[i] = t;
}

/**
 * `-magent -d<directory> -s<seed>`
 *
 * The seed is set here, through the game's own public call, so the run is
 * reproducible from the seed and the keys alone and no game file is patched
 * to arrange it (D6).
 */
errr init_agent(int argc, char *argv[])
{
    int i;

    for (i = 1; i < argc; i++) {
        if (prefix(argv[i], "-d")) {
            my_strcpy(agent_directory, argv[i] + 2, sizeof(agent_directory));
        } else if (prefix(argv[i], "-s")) {
            agent_seed = (uint32_t)strtoul(argv[i] + 2, NULL, 10);
            agent_seeded = true;
        } else {
            printf("init-agent: bad argument '%s'\n", argv[i]);
            return 1;
        }
    }

    if (agent_seeded) {
        Rand_quick = false;
        Rand_state_init(agent_seed);
    }

    agent_term_link(0);
    return 0;
}

const char help_agent[] = "Agent mode, subopts -d<directory> -s<seed>";

#endif /* USE_AGENT */
