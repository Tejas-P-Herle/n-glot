def to_str(word, state, re, match, **kwargs):

    word_map = state.conversions.conversions_space.word_map
    conversions = word_map[match[0]][match[1]]

    sanitized_word = re.sub("([\\[\\](){}*+?|^$.\\\\]){1}", r"\\\1", word)
    matcher = f"({sanitized_word})"

    if isinstance(conversions, str) or isinstance(conversions, dict):
        conversions = [conversions]

    for conversion in conversions:
        if isinstance(conversion, dict):
            matcher = re.sub(matcher, conversion["matcher"], word)
            if not re.match(matcher, word):
                continue
            conversion = conversion["conversion"]
        else:
            matcher = f"({sanitized_word})"
        return re.sub(matcher, conversion, word)

