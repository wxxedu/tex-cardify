import re

def single_group_parser(regex, data, pre_gen, sub_gen):
    children = _single_group_parser(regex, data)
    res = []
    for child in children:
        if child['title'] != '':
            res.append(pre_gen(child['data']))
        else:
            res.append(sub_gen(child['title'], child['data']))
    return res

def _single_group_parser(regex, data):
    children = []
    child = {'title': '', 'data': []}
    for line in data: 
        match = regex.match(line)
        if match:
            children.append(child)
            child = {'title': match.group(1), 'data': []}
        else:
            child['data'].append(line)
    return children

def latex_to_html_parser(data):
    data_str = ''.join(data)
    # separate out the $$...$$
    math_regex = re.compile(r'\$\$(.*)\$\$')
    math_matches = math_regex.findall(data_str) 
    for match in math_matches:
        # replace with placeholders
        data_str = data_str.replace('$$' + match + '$$', '¡¡¡MATH' +
                                    str(math_matches.index(match)) + 'MATH¡¡¡')
    # separate out the \begin{equation}...\end{equation}
    equation_regex = re.compile(r'\\begin\{(equation\*?)\}(.*)\\end\{\1\}')
    equation_matches = equation_regex.findall(data_str)
    for match in equation_matches:
        # replace with placeholders
        data_str = data_str.replace('\\begin{' + match[0] + '}' + match[1] + 
                                    '\\end{' + match[0] + '}',
                                    '¡¡¡EQUATION' + 
                                    str(equation_matches.index(match)) + 
                                    'EQUATION¡¡¡')
    # separate out the \begin{align}...\end{align}
    align_regex = re.compile(r'\\begin\{(align\*?)\}(.*)\\end\{\1\}')
    align_matches = align_regex.findall(data_str)
    for match in align_matches:
        # replace with placeholders
        data_str = data_str.replace('\\begin{' + match[0] + '}' + match[1] + 
                                    '\\end{' + match[0] + '}',
                                    '¡¡¡ALIGN' + 
                                    str(align_matches.index(match)) + 
                                    'ALIGN¡¡¡')
    # replace $...$ with <anki-mathjax>...</anki-mathjax>
    regexp = re.compile(r'\$(.*)\$')
    inline_matches = regexp.findall(data_str)
    for match in inline_matches:
        #replace with placeholders
        data_str = data_str.replace('$' + match + '$', '¡¡¡INLINEMATH' +
                                    str(inline_matches.index(match)) + 
                                    'INLINEMATH¡¡¡')
    # turn data_str into a list of lines
    data_lines = data_str.splitlines(True)
    tmp = []
    for line in data_lines:
        tmp.append(latex_to_html_line_parser(line))

    # join the lines back together
    data_str = ''.join(tmp)
    for match in inline_matches:
        escaped = match.replace('<', '&lt;').replace('>', '&gt;')
        # replace {{ with { { and }} with } }
        escaped = escaped.replace('{{', '{ {').replace('}}', '} }')
        data_str = data_str.replace('$' + match + '$', '<anki-mathjax>' +
                                    escaped + '</anki-mathjax>')
    # fill in the placeholders
    for match in math_matches:
        escaped = match.replace('<', '&lt;').replace('>', '&gt;')
        # replace {{ with { { and }} with } }
        escaped = escaped.replace('{{', '{ {').replace('}}', '} }')
        data_str = data_str.replace('¡¡¡MATH' + str(math_matches.index(match)) +
                                    'MATH¡¡¡', '<anki-mathjax block="true">' +
                                    escaped + '</anki-mathjax>')
    for match in equation_matches:
        escaped = match[1].replace('<', '&lt;').replace('>', '&gt;')
        # replace {{ with { { and }} with } }
        escaped = escaped.replace('{{', '{ {').replace('}}', '} }')
        data_str = data_str.replace('¡¡¡EQUATION' + 
                                    str(equation_matches.index(match)) +
                                    'EQUATION¡¡¡', '<anki-mathjax block="true">' +
                                    escaped + '</anki-mathjax>')
    for match in align_matches:
        escaped = match[1].replace('<', '&lt;').replace('>', '&gt;')
        # replace {{ with { { and }} with } }
        escaped = escaped.replace('{{', '{ {').replace('}}', '} }')
        data_str = data_str.replace('¡¡¡ALIGN' + 
                                    str(align_matches.index(match)) +
                                    'ALIGN¡¡¡', '<anki-mathjax block="true">' +
                                    r'\begin{aligned}' + escaped +
                                    r'\end{aligned}' + '</anki-mathjax>')
    return data_str

def latex_to_html_line_parser(line):
    bold_regex = re.compile(r'\\textbf\{(.*)\}')
    # replace bold with <b> and </b>
    matches = bold_regex.findall(line)
    for match in matches:
        line = line.replace('\\textbf{' + match + '}', '<b>' + match + '</b>')
    # replace italic with <i> and </i>
    italic_regex = re.compile(r'\\textit\{(.*)\}')
    matches = italic_regex.findall(line)
    for match in matches:
        line = line.replace('\\textit{' + match + '}', '<i>' + match + '</i>')
    # replace underline with <u> and </u>
    underline_regex = re.compile(r'\\underline\{(.*)\}')
    matches = underline_regex.findall(line)
    for match in matches:
        line = line.replace('\\underline{' + match + '}', '<u>' + match + '</u>')
    # replace texttt with <code> and </code>
    texttt_regex = re.compile(r'\\texttt\{(.*)\}')
    matches = texttt_regex.findall(line)
    for match in matches:
        line = line.replace('\\texttt{' + match + '}', '<code>' + match + '</code>')
    # replace \begin{itemize} with <ul>
    line = line.replace('\\begin{itemize}', '<ul>')
    # replace \end{itemize} with </ul>
    line = line.replace('\\end{itemize}', '</ul>')
    # replace enumerate with <ol>
    line = line.replace('\\begin{enumerate}', '<ol>')
    # replace \end{enumerate} with </ol>
    line = line.replace('\\end{enumerate}', '</ol>')
    # replace \item with <li>
    line = line.replace('\\item', '<li>')
    # replace center with <div class="center">
    line = line.replace('\\begin{center}', '<div class="center">')
    # replace \end{center} with </div>
    line = line.replace('\\end{center}', '</div>')
    # replace \begin{proof} with <b><i>proof.</i></b>
    line = line.replace('\\begin{proof}', '<div class="proof"><b><i>proof.</i></b>')
    # replace \end{proof} with <div class="qed"></div></div>
    line = line.replace('\\end{proof}', '<div class="qed"></div></div>')
    return line
