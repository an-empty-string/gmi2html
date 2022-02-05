import enum
import html
import sys


class ParserState(enum.Enum):
    NORMAL = enum.auto()
    LINK = enum.auto()
    LIST = enum.auto()
    BLOCKQUOTE = enum.auto()
    HEADER_1 = enum.auto()
    HEADER_2 = enum.auto()
    HEADER_3 = enum.auto()
    PREFORMATTED = enum.auto()


parent_tags = {
    ParserState.LIST: "ul",
    ParserState.BLOCKQUOTE: "blockquote",
    ParserState.PREFORMATTED: "pre",
}

tags = {
    ParserState.NORMAL: "p",
    ParserState.LIST: "li",
    ParserState.BLOCKQUOTE: "p",
    ParserState.HEADER_1: "h1",
    ParserState.HEADER_2: "h2",
    ParserState.HEADER_3: "h3",
}

shorthands = {
    "---": "&mdash;",
    "--": "&ndash;",
}


def transition(last_state, state):
    result = []
    if last_state != state:
        result.extend([exit_state(last_state), enter_state(state)])

    return list(filter(None, result))


def enter_state(state):
    if state in parent_tags:
        return f"<{parent_tags[state]}>"


def exit_state(state):
    if state in parent_tags:
        return f"</{parent_tags[state]}>"


def gmi2html(lines):
    last_state = ParserState.NORMAL
    state = ParserState.NORMAL

    last_is_linebreak = False

    result = [
        "<style>a { display: block; }</style>"
    ]

    for line in lines:
        text = None

        if state == ParserState.PREFORMATTED:
            if line == "```":
                state = ParserState.NORMAL

            else:
                text = line

        elif line.startswith("*"):
            state = ParserState.LIST
            text = line[1:].strip()

        elif line.startswith(">"):
            state = ParserState.BLOCKQUOTE
            text = line[1:].strip()

        elif line.startswith("```"):
            state = ParserState.PREFORMATTED

        elif line.startswith("###"):
            state = ParserState.HEADER_3
            text = line[3:].strip()

        elif line.startswith("##"):
            state = ParserState.HEADER_2
            text = line[2:].strip()

        elif line.startswith("#"):
            state = ParserState.HEADER_1
            text = line[1:].strip()

        elif line.startswith("=>"):
            state = ParserState.LINK

            link = text = line[2:].strip()
            if " " in text:
                link, text = text.split(" ", maxsplit=1)
                text = text.strip()

        else:
            state = ParserState.NORMAL
            text = line.strip()

        cresult = transition(last_state, state)

        indent_level = 2 if state in parent_tags else 0
        indent = " " * indent_level

        is_linebreak = False

        if text is not None:
            escaped_text = html.escape(text)

            if state != ParserState.PREFORMATTED:
                for k, v in shorthands.items():
                    escaped_text = escaped_text.replace(k, v)

            if text == "" and state == ParserState.NORMAL and last_state == ParserState.NORMAL:
                is_linebreak = True
                cresult.append(f"{indent}<br />")

            elif state == ParserState.LINK:
                if last_is_linebreak:
                    result.pop()

                cresult.append(
                    f'{indent}<a href="{html.escape(link)}">{escaped_text}</a>')

            else:
                if last_is_linebreak and state not in (ParserState.PREFORMATTED,):
                    result.pop()

                tag = tags.get(state)

                if tag is not None:
                    cresult.append(f"{indent}<{tag}>{escaped_text}</{tag}>")
                else:
                    cresult.append(f"{text}")

        last_state = state
        last_is_linebreak = is_linebreak
        result.extend(cresult)

    return result


if __name__ == "__main__":
    import sys
    for line in gmi2html(line.rstrip("\r\n") for line in sys.stdin):
        sys.stdout.write(f"{line}\n")
