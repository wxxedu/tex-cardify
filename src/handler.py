from os import path
from aqt import mw 

def gen_handler(name: str):
    deck_id = mw.col.decks.id(name)
    card_model = mw.col.models.byName("Basic")
    mw.col.decks.select(deck_id)
    mw.col.models.setCurrent(card_model)
    def handler(front: str, back: str):
        note = mw.col.newNote()
        note['Front'] = front
        note['Back'] = back 
        mw.col.add_note(note, deck_id=deck_id)
        mw.col.flush()
    return handler

def gen_gen_handler(base_deck: str):
    def h(name: str): 
        if (name == ""):
            return gen_handler(base_deck) 
        else:
            return gen_handler(base_deck + "::" + name)
    return h

def gen_file_handler(base_path: str):
    def file_handler(name: str) -> str:
        p = path.join(base_path, name)
        return mw.col.media.addFile(p)
    return file_handler
