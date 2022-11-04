from .section_parser import latex_to_html_parser, single_group_parser
from aqt import mw
import re

class Node: 
    def __init__(self, data, children, node_type) -> None:
        self.data = data
        self.children = children
        self.node_type = node_type

    def act(self, name, **kwargs):
        for child in self.children:
            child.act(name, **kwargs)

class FileNode(Node): 
    def __init__(self, data): 
        super().__init__(data, [], 'file')
        self.parse()

    def parse(self):
        regex = re.compile(r'\\section\*?\{(.*)\}')
        self.children = single_group_parser(
                regex, self.data, QnAListNode, SectionNode)
        

    def act(self, name, **kwargs):
        
        for child in self.children:
            child.act(name, **kwargs)


class SectionNode(Node):
    def __init__(self, title, data): 
        super().__init__(data, [], 'section')
        self.title = title
        self.parse()
    
    def parse(self):
        regex = re.compile(r'\\subsection\*?\{(.*)\}')
        self.children = single_group_parser(
                regex, self.data, QnAListNode, SubsectionNode)

    
    def act(self, name, **kwargs):
        
        for child in self.children:
            child.act(f'{name}::{self.title}', **kwargs)

class SubsectionNode(Node):
    def __init__(self, title, data): 
        super().__init__(data, [], 'subsection')
        self.title = title 
        self.parse()

    def parse(self):
        regex = re.compile(r'\\subsubsection\*?\{(.*)\}')
        self.children = single_group_parser(
                regex, self.data, QnAListNode, SubsubsectionNode)

    
    def act(self, name, **kwargs):
        
        for child in self.children:
            child.act(f'{name}::{self.title}', **kwargs)

class SubsubsectionNode(Node):
    def __init__(self, title, data): 
        super().__init__(data, [], 'subsubsection')
        self.title = title
        self.parse()

    def parse(self):
        self.children = [QnAListNode(self.data)]

    
    def act(self, name, **kwargs):
        
        for child in self.children:
            child.act(f'{name}::{self.title}', **kwargs)

class QnAListNode(Node):
    def __init__(self, data): 
        super().__init__(data, [], 'qna_list')
        self.parse()

    def parse(self):
        regex = re.compile(r'\\begin\{(cst.*)\}')
        self.children = single_group_parser(
                regex, self.data, NoOpNode, QnANode)
        

    
    def act(self, name, **kwargs):
        for child in self.children:
            child.act(name, **kwargs)

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
        regex = re.compile(r'\\end\{(cst.*)\}')
        for line in self.data:
            if (is_front):
                if (regex.search(line)):
                    is_front = False
                else: 
                    self.front.append(line)
            else: 
                self.back.append(line)

    def get_front(self, base_url):
        return latex_to_html_parser(self.front, base_url, self.img_mover)

    def get_back(self, base_url):
        return latex_to_html_parser(self.back, base_url, self.img_mover)

    
    def act(self, name, **kwargs):
        deck_id = mw.col.decks.id(name)
        card_model = mw.col.models.byName('Basic')
        mw.col.decks.select(deck_id)
        mw.col.models.setCurrent(card_model)
        note = mw.col.newNote()
        note['Front'] = self.get_front(kwargs['base_url'])
        note['Back'] = self.get_back(kwargs['base_url'])
        mw.col.add_note(note, deck_id=deck_id)
        mw.col.flush()

    def img_mover(self, path):
        # read the media folder of the current user from anki 
        return mw.col.media.addFile(path)

"""
if __name__ == "__main__":
    # read ../data/test.tex
    data = []
    with open('../data/test.tex', 'r') as f:
        data = f.readlines()
    file_node = FileNode(data)
    file_node.act('test')
"""
