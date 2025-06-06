def combine_ansi_horizontally(*streams) -> str:
    lines_list = [s.splitlines() for s in streams]
    out = ""
    for line_group in zip(*lines_list):
        out += ''.join(line_group) + '\n'
    return out
