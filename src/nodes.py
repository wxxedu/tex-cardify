from section_parser import latex_to_html_parser, single_group_parser
import re

class Node: 
    def __init__(self, data, children, node_type) -> None:
        self.data = data
        self.children = children
        self.node_type = node_type
    
class FileNode(Node): 
    def __init__(self, data): 
        super().__init__(data, [], 'file')
        self.parse()

    def parse(self):
        regex = re.compile(r'\section\*?\{(.*)\}')
        self.children = single_group_parser(
                regex, self.data, QnAListNode, SectionNode)

class SectionNode(Node):
    def __init__(self, title, data): 
        super().__init__(data, [], 'section')
        self.title = title
        self.parse()
    
    def parse(self):
        regex = re.compile(r'\subsection\*?\{(.*)\}')
        self.children = single_group_parser(
                regex, self.data, QnAListNode, SubsectionNode)

class SubsectionNode(Node):
    def __init__(self, title, data): 
        super().__init__(data, [], 'subsection')
        self.title = title 
        self.parse()

    def parse(self):
        regex = re.compile(r'\subsubsection\*?\{(.*)\}')
        self.children = single_group_parser(
                regex, self.data, QnAListNode, SubsubsectionNode)

class SubsubsectionNode(Node):
    def __init__(self, title, data): 
        super().__init__(data, [], 'subsubsection')
        self.title = title
        self.parse()

    def parse(self):
        self.children = [QnAListNode(self.data)]

class QnAListNode(Node):
    def __init__(self, data): 
        super().__init__(data, [], 'qna_list')
        self.parse()

    def parse(self):
        regex = re.compile(r'\begin\{(cst.*)\}')
        self.children = single_group_parser(
                regex, self.data, NoOpNode, QnANode)

class NoOpNode(Node):
    def __init__(self, data): 
        super().__init__(data, [], 'noop')


class QnANode(Node): 
    def __init__(self, qna_type, data): 
        super().__init__(data, [], 'qna')
        self.qna_type = qna_type
        self.front = []
        self.back = []
        self.parse()

    def parse(self):
        is_front = True
        regex = re.compile(r'\begin\{' + self.qna_type + r'\}')
        for line in self.data:
            if (is_front):
                if (regex.match(line)):
                    is_front = False
                else: 
                    self.front.append(line)
            else: 
                self.back.append(line)

    def get_front(self):
        return latex_to_html_parser(self.front)

    def get_back(self):
        return latex_to_html_parser(self.back)
        
