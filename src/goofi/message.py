from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict

from goofi.connection import Connection
from goofi.data import Data


class MessageType(Enum):
    """
    The type of a message. The message type determines the content of the message.

    - `ADD_OUTPUT_PIPE`: Sent by the manager to a node to add an output pipe to an output slot.
        - `slot_name_out` (str): The name of the output slot.
        - `slot_name_in` (str): The name of the input slot.
        - `node_connection` (Connection): The connection object to the node.
    - `REMOVE_OUTPUT_PIPE`: Sent by the manager to a node to remove an output pipe from an output slot.
        - `slot_name_out` (str): The name of the output slot.
        - `slot_name_in` (str): The name of the input slot.
        - `node_connection` (Connection): The connection object to the node.
    - `DATA`: Sent by one node to another and contains data sent from an output slot to an input slot.
        - `slot_name` (str): The name of the target input slot.
        - `data` (Data): The data object. See the `Data` class for more information.
    - `CLEAR_DATA`: Clear the data field on an input slot.
    - `PING`: Empty probe to check if a process is alive.
    - `PONG`: Response to a ping message.
    - `TERMINATE`: Empty message to indicate that a node should terminate.
    """

    ADD_OUTPUT_PIPE = 1
    REMOVE_OUTPUT_PIPE = 2
    DATA = 3
    CLEAR_DATA = 4
    PING = 5
    PONG = 6
    TERMINATE = 7


@dataclass
class Message:
    """
    A message is used to send information between nodes. Each message has a type and some content. The
    content field is a dict that contains the message content. The content field must contain the correct
    fields for the message type.

    ### Parameters
    `type` : MessageType
        The type of the message.
    `content` : Dict[str, Any]
        The content of the message with required fields for the message type.
    """

    type: MessageType
    content: Dict[str, Any]

    def require_fields(self, **fields: Dict[str, Any]) -> None:
        """
        Check that the message content contains the required fields.

        ### Parameters
        `fields` : Dict[str, Any]
            A dictionary of required fields and their types.
        """
        for field, field_type in fields.items():
            if field not in self.content:
                raise ValueError(f"Message content must contain field {field}.")
            if not isinstance(self.content[field], field_type):
                raise ValueError(
                    f"Message content field {field} must be of type {field_type} but got {type(self.content[field])}."
                )

    def __post_init__(self):
        """
        Check that the message content is valid. The content field must be a dict, and it must contain the correct
        fields for the message type.
        """
        # general checks
        if self.type is None:
            raise ValueError("Expected message type, got None.")
        if not isinstance(self.content, dict):
            raise ValueError(f"Expected dict, got {type(self.content)}.")

        # check the content for the specific message type
        if self.type == MessageType.ADD_OUTPUT_PIPE:
            self.require_fields(slot_name_out=str, slot_name_in=str, node_connection=Connection)
        elif self.type == MessageType.REMOVE_OUTPUT_PIPE:
            self.require_fields(slot_name_out=str, slot_name_in=str, node_connection=Connection)
        elif self.type == MessageType.DATA:
            self.require_fields(slot_name=str, data=Data)
        elif self.type == MessageType.CLEAR_DATA:
            self.require_fields(slot_name=str)
