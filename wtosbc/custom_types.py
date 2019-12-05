from typing import Any, List, Dict, Optional
from mypy_extensions import TypedDict


class OrderItem(TypedDict):
    url: str
    type: str
    qty: int
    pa: str
    id: str
    type_id: str
    price: float
    original_price: float
    name: bytes


Orders = Dict[str, List[Optional[OrderItem]]]


class State(TypedDict):
    number: int
    pa: bool
    state: bool


class ProductData(TypedDict):
    id: str
    name: bytes
    qty: str
    pa: str
    type: str
    price: float
    type_id: str
    token: str


class Product(TypedDict):
    url: str
    type: str
    qty: int
    pa: str


ProductsPerUser = Dict[str, List[Product]]

Session = Any


class Post(TypedDict):
    post_content: str
    display_name: str


Posts = List[Post]
