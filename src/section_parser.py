import re
from os import path
#from aqt.utils import showInfo

def single_group_parser(regex, data, pre_gen, sub_gen):
    children = _single_group_parser(regex, data)
    res = []
    for child in children:
        if child['title'] == '':
            res.append(pre_gen(child['data']))
        else:
            res.append(sub_gen(child['title'], child['data']))
    return res

def _single_group_parser(regex, data):
    children = []
    child = {'title': '', 'data': []}
    for line in data:
        match = regex.search(line)
        if match:
            children.append(child)
            child = {'title': match[1], 'data': []}
        else:
            child['data'].append(line)
    children.append(child)
    return children

def latex_to_html_parser(data, base_url, img_mover):
    data_str = ''.join(data)
    # escape 
    data_str = data_str.replace('&', '&amp;')
    data_str = data_str.replace('<', '&lt;')
    data_str = data_str.replace('>', '&gt;')
    # separate out the $$...$$ ignore new lines
    math_regex = re.compile(r'\$\$([^\$]+)\$\$', re.MULTILINE)
    math_matches = math_regex.findall(data_str) 
    for match in math_matches:
        # replace with placeholders
        data_str = data_str.replace('$$' + match + '$$', '¡¡¡MATH' +
                                    str(math_matches.index(match)) + 'MATH¡¡¡')
    # separate out the \begin{equation}...\end{equation}
    equation_regex = re.compile(r'\\begin\{(equation\*?)\}([\s\S]*?)\\end\{\1\}', re.MULTILINE)
    equation_matches = equation_regex.findall(data_str)
    for match in equation_matches:
        # replace with placeholders
        data_str = data_str.replace('\\begin{' + match[0] + '}' + match[1] + 
                                    '\\end{' + match[0] + '}',
                                    '¡¡¡EQUATION' + 
                                    str(equation_matches.index(match)) + 
                                    'EQUATION¡¡¡')
    # separate out the \begin{align}...\end{align}
    align_regex = re.compile(r'\\begin\{(align\*?)\}([\s\S]*?)\\end\{\1\}', re.MULTILINE)
    align_matches = align_regex.findall(data_str)
    for match in align_matches:
        # replace with placeholders
        data_str = data_str.replace('\\begin{' + match[0] + '}' + match[1] + 
                                    '\\end{' + match[0] + '}',
                                    '¡¡¡ALIGN' + 
                                    str(align_matches.index(match)) + 
                                    'ALIGN¡¡¡')
    # replace $...$ with <anki-mathjax>...</anki-mathjax>
    regexp = re.compile(r'\$([\s\S]*?)\$', re.MULTILINE)
    inline_matches = regexp.findall(data_str)
    for match in inline_matches:
        #replace with placeholders
        data_str = data_str.replace('$' + match + '$', '¡¡¡INLINEMATH' +
                                    str(inline_matches.index(match)) +
                                    'INLINEMATH¡¡¡')

    ################### Intermediate ###################

    regexp = re.compile(r'\\cimg\{([\s\S]*?)\}', re.MULTILINE)
    img_matches = regexp.findall(data_str)
    for match in img_matches:
        # get the new name
        try:
            new_name = img_mover(path.join(base_url, match[0]))
            data_str = data_str.replace('\\cimg{' + match + '}', 
                                    '<img src="' + new_name + '">')
        except:
            data_str = data_str.replace('\\cimg{' + match + '}', '')
    
    regexp = re.compile(r'\\includegraphics\[([\s\S]*?)\]\{([\s\S]*?)\}', re.MULTILINE)
    img_matches = regexp.findall(data_str)
    for match in img_matches:
        # get the new name
        try:
            new_name = img_mover(path.join(base_url, match[1]))
            data_str = data_str.replace('\\includegraphics[' + match[0] +
                                    ']{' + match[1]+ '}', '<img src="' +
                                    new_name + '" />')
        except:
            data_str = data_str.replace('\\includegraphics[' + match[0] +
                                    ']{' + match[1]+ '}', '')

    regexp = re.compile(r'\\textbf\{([\s\S]*?)\}', re.MULTILINE)
    data_str = regexp.sub(r'<b>\1</b>', data_str, re.MULTILINE)


    # replace \textit{...} with <i>...</i>
    regexp = re.compile(r'\\textit\{([\s\S]*?)\}', re.MULTILINE)
    data_str = regexp.sub(r'<i>\1</i>', data_str, re.MULTILINE)

    # replace \texttt{...} with <code>...</code>
    regexp = re.compile(r'\\texttt\{([\s\S]*?)\}', re.MULTILINE)
    data_str = regexp.sub(r'<code>\1</code>', data_str, re.MULTILINE)

    # replace \begin{itemize} with <ul>
    data_str = data_str.replace('\\begin{itemize}', '<ul>')
    # replace \end{itemize} with </ul>
    data_str = data_str.replace('\\end{itemize}', '</ul>')
    # replace enumerate with <ol>
    data_str = data_str.replace('\\begin{enumerate}', '<ol>')
    # replace \end{enumerate} with </ol>
    data_str = data_str.replace('\\end{enumerate}', '</ol>')
    # replace \item with <li>
    data_str = data_str.replace('\\item', '<li>')
    # replace center with <div class="center">
    data_str = data_str.replace('\\begin{center}', '<div class="center">')
    # replace \end{center} with </div>
    data_str = data_str.replace('\\end{center}', '</div>')
    # replace \begin{proof} with <b><i>proof.</i></b>
    data_str = data_str.replace('\\begin{proof}', '<div class="proof"><b><i>proof.</i></b>')
    # replace \end{proof} with <div class="qed"></div></div>
    data_str = data_str.replace('\\end{proof}', '<div class="qed"></div></div>')
    
    ############### Reassemble #############
    for match in inline_matches:
        escaped = match.replace('{{', '{ {').replace('}}', '} }')
        data_str = data_str.replace('¡¡¡INLINEMATH' +
                                    str(inline_matches.index(match)) + 
                                    'INLINEMATH¡¡¡', r'\(' +
                                    escaped + r'\)')
    # fill in the placeholders
    for match in math_matches:
        escaped = match.replace('{{', '{ {').replace('}}', '} }')
        data_str = data_str.replace('¡¡¡MATH' + str(math_matches.index(match)) +
                                    'MATH¡¡¡', r'\[' +
                                    escaped + r'\]')
    for match in equation_matches:
        # replace {{ with { { and }} with } }
        escaped = match.replace('{{', '{ {').replace('}}', '} }')
        data_str = data_str.replace('¡¡¡EQUATION' + 
                                    str(equation_matches.index(match)) +
                                    'EQUATION¡¡¡', r'\[' +
                                    escaped + r'\]')
    for match in align_matches:
        # replace {{ with { { and }} with } }
        escaped = match.replace('{{', '{ {').replace('}}', '} }')
        data_str = data_str.replace('¡¡¡ALIGN' + 
                                    str(align_matches.index(match)) +
                                    'ALIGN¡¡¡', r'\[' +
                                    r'\begin{aligned}' + escaped +
                                    r'\end{aligned}' + r'\]')
    return data_str

