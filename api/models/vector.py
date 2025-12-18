from pydantic import BaseModel

class postDocument(BaseModel):
    '''Schema for posting a document to be embedded.'''                     
    text: str

class searchQuery(BaseModel):
    '''Schema for search query.'''
    query: str
    k: int