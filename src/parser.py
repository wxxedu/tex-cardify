from re import Pattern, compile
import markdown2

################ Utils ################

class Parser: 
    def parse(self, text: str) -> str:
        return text

class Pair:
    """Pair of objects"""
    def __init__(self, first, second):
        self.first = first
        self.second = second

    def __repr__(self):
        return f"Pair({self.first}, {self.second})"

    def transform_first(self, f):
        return Pair(f(self.first), self.second)

    def transform_second(self, f):
        return Pair(self.first, f(self.second))

def split_regex(text: str, regex: Pattern) -> list: 
    """
    Split text by regex
    It returns a list of Pair objects, with the first one being the match 
    object and the second one being the string after the match and before the 
    next match
    """
    # find all matches 
    matches = regex.finditer(text)
    res = []
    # reverse the matches 
    for match in reversed(list(matches)):
        tmp = text.split(match.group())
        text = tmp[0] 
        res.append(Pair(match, tmp[1]))
    if (text.strip() != ""):
        res.append(Pair(None, text))
    # reverse the result 
    return list(reversed(res))

lmap = lambda f, *iterables: list(map(f, *iterables))

################ Section Parser ################

def _split_core(text: str, regex: Pattern) -> list: 
    return lmap(lambda p: p.transform_first(lambda s: s.group(1)), 
                split_regex(text, regex))

def split_sections(text: str) -> list: 
    regex = compile(r"\\section(?:\*)?\{(.*?)\}")
    return _split_core(text, regex)

def split_subsections(text: str) -> list: 
    regex = compile(r"\\subsection(?:\*)?\{(.*?)\}") 
    return _split_core(text, regex)

def split_subsubsections(text: str) -> list: 
    regex = compile(r"\\subsubsection(?:\*)?\{(.*?)\}") 
    return _split_core(text, regex)

################ Environment Parser ################ 

class NestedParser(Parser):
    def __init__(self, imp) -> None:
        super().__init__()
        self.imp = imp

class ProtectedEnvironmentParser(NestedParser):
    def __init__(self, regex: Pattern, assembler, imp: Parser) -> None:
        """
        begin: regex for the begin of the environment 
        end: regex for the end of the environment 
        imp: intermediate parser
        """
        super().__init__(imp)
        self.regex = regex 
        self.assembler = assembler 
        self.imp = imp
        self.tmp = []

    def parse(self, text: str) -> str:
        self.tmp = []
        text = self._parse(text) 
        text = self.imp.parse(text)
        text = self._assemble(text)
        return text

    def _parse(self, text: str) -> str:
        """
        begin([\\s\\S]*?)end 
        """
        self.tmp = list(self.regex.finditer(text))
        count = 0
        for match in self.tmp:
            # replace the match with a placeholder 
            text = text.replace(match.group(),
                                f"__{hash(self)}_{count}__")
            count += 1
        return text

    def _assemble(self, text: str) -> str: 
        for i, match in enumerate(self.tmp):
            text = text.replace(f"__{hash(self)}_{i}__", self.assembler(match))
        return text

class UnprotectedEnvironmentParser(Parser):
    def __init__(self, regex: Pattern, assembler) -> None:
        super().__init__()
        self.regex = regex 
        self.assembler = assembler

    def parse(self, text: str) -> str: 
        matches = list(self.regex.finditer(text)) 
        for match in matches: 
            text = text.replace(match.group(), self.assembler(match)) 
        return text

class SimpleReplacementParser(Parser): 
    def __init__(self, fstr: str, tstr: str) -> None:
        super().__init__()
        self.fstr = fstr 
        self.tstr = tstr 

    def parse(self, text: str) -> str: 
        return text.replace(self.fstr, self.tstr)

class SequentialParser(Parser):
    def __init__(self, parsers: list) -> None:
        super().__init__()
        self.parsers = parsers 

    def parse(self, text: str) -> str:
        for parser in self.parsers:
            text = parser.parse(text)
        return text

################ Parsers ################

noop = Parser()

def escape(text: str) -> str:
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    text = text.replace("{{", "{ {")
    text = text.replace("}}", "} }")
    return text

################ Unprotected Parsers ################

parsers = []

# escape

_escape_parser_1 = SimpleReplacementParser("&", "&amp;")
_escape_parser_2 = SimpleReplacementParser("<", "&lt;")
_escape_parser_3 = SimpleReplacementParser(">", "&gt;")
escape_parser = SequentialParser([_escape_parser_1, _escape_parser_2, _escape_parser_3])
parsers.append(escape_parser)

# line parser - replace \n\n with <br> and \n with " "

line_parser = SimpleReplacementParser("\n\n", "<br>")
line_parser = SequentialParser([line_parser, SimpleReplacementParser("\n", " ")])
parsers.append(line_parser)

# center

center_regex = compile(r"\\begin\{center\}([\s\S]*?)\\end\{center\}")
center_assembler = lambda match: r'<div class="tex-center">' + match.group(1) + r"</div>"
center_parser = UnprotectedEnvironmentParser(center_regex, center_assembler)
parsers.append(center_parser)

# proof

proof_regex = compile(r"\\begin\{proof\}([\s\S]*?)\\end\{proof\}") 
_proof_start = r'<div class="tex-proof"><span class="tex-proof-start">Proof.</span>'
_proof_end = r'<div class="tex-proof-end"></div></div>'
proof_assembler = lambda match: _proof_start + match.group(1) + r"</div>" + _proof_end
proof_parser = UnprotectedEnvironmentParser(proof_regex, proof_assembler)
parsers.append(proof_parser)

# styles 

bold_regex = compile(r"\\textbf\{([\s\S]*?)\}") 
bold_assembler = lambda match: f'<span class="tex-bold">{match.group(1)}</span>'
bold_parser = UnprotectedEnvironmentParser(bold_regex, bold_assembler)

italic_regex = compile(r"\\textit\{([\s\S]*?)\}") 
italic_assembler = lambda match: f'<span class="tex-italic">{match.group(1)}</span>'
italic_parser = UnprotectedEnvironmentParser(italic_regex, italic_assembler) 

underline_regex = compile(r"\\underline\{([\s\S]*?)\}") 
underline_assembler = lambda match: f'<span class="tex-underline">{match.group(1)}</span>'
underline_parser = UnprotectedEnvironmentParser(underline_regex, underline_assembler)

code_regex = compile(r"\\texttt\{([\s\S]*?)\}")
code_assembler = lambda match: f'<span class="tex-code">{match.group(1)}</span>'
code_parser = UnprotectedEnvironmentParser(code_regex, code_assembler)

parsers += [bold_parser, italic_parser, underline_parser, code_parser]

# lists

itemize_regex = compile(r"\\begin\{itemize\}([\s\S]*?)\\end\{itemize\}")
itemize_assembler = lambda match: r'<ul class="tex-itemize"><li style="display:none;">' + match.group(1) + r"</li></ul>"
itemize_parser = UnprotectedEnvironmentParser(itemize_regex, itemize_assembler)
enumerate_regex = compile(r"\\begin\{enumerate\}([\s\S]*?)\\end\{enumerate\}")
enumerate_assembler = lambda match: r'<ol class="tex-enumerate"><li style="display:none;">' + match.group(1) + r"</li></ol>"
enumerate_parser = UnprotectedEnvironmentParser(enumerate_regex, enumerate_assembler)
item_parser = SimpleReplacementParser(r"\item", r"</li><li>")
parsers += [itemize_parser, enumerate_parser, item_parser]

# paragraph parser 

paragraph_regex = compile(r"\\paragraph\{(.+?)\}")
paragraph_assembler = lambda match: '<span class="tex-paragraph">' + match.group(1) + "</span>"
paragraph_parser = UnprotectedEnvironmentParser(paragraph_regex, paragraph_assembler)
parsers.append(paragraph_parser)

# sequential aggregate 

unprotected_parser = SequentialParser(parsers)

################ Protected Parsers ################

inline_math_regex = compile(r"\$([\s\S]*?)\$")
inline_math_assembler = lambda match: f"\\({escape(match.group(1))}\\)"
inline_math_parser = ProtectedEnvironmentParser(inline_math_regex,
                                                inline_math_assembler, unprotected_parser) 

block_math_assembler = lambda match: f"\\[{escape(match.group(1))}\\]" 
display_math_regex = compile(r"\$\$([\s\S]*?)\$\$") 
display_math_parser = ProtectedEnvironmentParser(display_math_regex, 
                                                 block_math_assembler, inline_math_parser)

equation_regex = compile(r"\\begin\{equation\*?\}([\s\S]*?)\\end\{equation\*?\}")
equation_parser = ProtectedEnvironmentParser(equation_regex, 
                                             block_math_assembler, display_math_parser)

gather_regex = compile(r"\\begin\{gather\*?\}([\s\S]*?)\\end\{gather\*?\}")
gather_assembler = lambda match: r"\[\begin{gathered}" + escape(match.group(1)) + r"\end{gathered}\]"
gather_parser = ProtectedEnvironmentParser(gather_regex, gather_assembler, 
                                           equation_parser)

align_regex = compile(r"\\begin\{align\*?\}([\s\S]*?)\\end\{align\*?\}")
align_assembler = lambda match: r"\[\begin{aligned}" + escape(match.group(1)) + r"\end{aligned}\]"
align_parser = ProtectedEnvironmentParser(align_regex, align_assembler, gather_parser)

minted_regex = compile(r"\\begin\{minted\*?\}(?:\[[\s\S]*\])?\{([\s\S]*?)\}([\s\S]*?)\\end\{minted\*?\}")
code_md_assembler = lambda match: r"```" + match.group(1) + "\n" + escape(match.group(2)) + r"\n```"
minted_assembler = lambda match: markdown2.markdown(code_md_assembler(match), extras=["fenced-code-blocks"])
minted_parser = ProtectedEnvironmentParser(minted_regex, minted_assembler, align_parser)

image_regex = compile(r"\\includegraphics(?:\[[\s\S]*\])?\{([\s\S]*?)\}")
image_assembler = lambda match: r"![](" + match.group(1) + ")"
image_parser = ProtectedEnvironmentParser(image_regex, image_assembler, minted_parser)

# parser 
parser = image_parser

################# Custom Section Parser #################

def split_cst(text: str, handler): 
    cst_regex = compile(r"\\begin\{cst(.*?)\}(?:\{([\s\S]*?)\})?([\s\S]*?)\\end\{cst(.*?)\}")
    splits = split_regex(text, cst_regex)
    for split in splits: 
        handle_split(split, handler)

def handle_split(split, handler):
    first = split.first
    split_type = first.group(1)
    representationStr = ""
    if split_type == "def":
        representationStr = r'<span class="text-cst, text-cst-def">Definition ' + first.group(2) + r".</span>"
    elif split_type == "def*":
        representationStr = r'<span class="text-cst, text-cst-def">Definition.</span>'
    elif split_type == "thm":
        representationStr = r'<span class="text-cst, text-cst-thm">Theorem ' + first.group(2) + r".</span>"
    elif split_type == "thm*":
        representationStr = r'<span class="text-cst, text-cst-thm">Theorem.</span>'
    elif split_type == "eg":
        representationStr = r'<span class="text-cst, text-cst-eg">Example ' + first.group(2) + r".</span>"
    elif split_type == "eg*":
        representationStr = r'<span class="text-cst, text-cst-eg">Example.</span>'
    elif split_type == "exe":
        representationStr = r'<span class="text-cst, text-cst-exe">Exercise ' + first.group(2) + r".</span>"
    elif split_type == "exe*":
        representationStr = r'<span class="text-cst, text-cst-exe">Exercise.</span>'
    elif split_type == "eexe":
        representationStr = r'<span class="text-cst, text-cst-eexe">Extra Exercise ' + first.group(2) + r".</span>"
    elif split_type == "eexe*":
        representationStr = r'<span class="text-cst, text-cst-eexe">Extra Exercise.</span>'
    elif split_type == "rmk":
        representationStr = r'<span class="text-cst, text-cst-rmk">Remark ' + first.group(2) + r".</span>"
    elif split_type == "rmk*":
        representationStr = r'<span class="text-cst, text-cst-rmk">Remark.</span>'
    elif split_type == "qsn":
        representationStr = r'<span class="text-cst, text-cst-qsn">Question ' + first.group(2) + r".</span>"
    elif split_type == "qsn*":
        representationStr = r'<span class="text-cst, text-cst-qsn">Question.</span>'
    elif split_type == "cor":
        representationStr = r'<span class="text-cst, text-cst-cor">Corollary ' + first.group(2) + r".</span>"
    elif split_type == "cor*":
        representationStr = r'<span class="text-cst, text-cst-cor">Corollary.</span>'
    else:
        representationStr = ""
    front_text = representationStr + parser.parse(first.group(3))
    back_text = parser.parse(split.second)
    handler(front_text, back_text)

################ Parse All ################

def parse_all(text: str, handler_gen): 
    sections = split_sections(text)
    for section in sections: 
        name = ""
        if section.first is None:
            split_cst(section.second, handler_gen(name))
            continue
        else:
            name = section.first
        subsections = split_subsections(section)
        for subsection in subsections: 
            subname = ""
            if subsection.first is None:
                subname = name 
                split_cst(subsection.second, handler_gen(subname))
                continue
            else: 
                subname = name + "::" + subsection.first
            subsubsections = split_subsubsections(subsection)
            for subsubsection in subsubsections: 
                subsubname = ""
                if subsubsection.first is None:
                    subsubname = subname 
                    split_cst(subsubsection.second, handler_gen(subsubname))
                    continue
                else: 
                    subsubname = subname + "::" + subsubsection.first
                split_cst(subsubsection.second, handler_gen(subsubname))


################ Tests ################
if __name__ == "__main__":
    with open("lec11.tex", "r") as f:
        tex = f.read()
    html = parser.parse(tex)
    with open("lec11.html", "w") as f:
        f.write(html)

