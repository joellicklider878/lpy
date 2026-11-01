
import re

class Token:
    # Token Type Constants
    DEFINE = 'DEFINE'
    AS = 'AS'
    CALL = 'CALL'
    WITH = 'WITH'
    IDENTIFIER = 'IDENTIFIER'
    STRING = 'STRING'

    def __init__(self, type_: str, value: str):
        self.type = type_    # e.g., 'DEFINE' or 'STRING'
        self.value = value  # e.g., 'target' or '192.168.1.10'

    def __repr__(self):
        return f"Token({self.type}, '{self.value}')"

    @staticmethod
    def lex(text: str) -> list:
        tokens = []
        
        # updated to allow dots in identifiers
        token_specification = r'"[^"]*"|\'[^\']*\'|[\w.]+'
        
        for line in text.splitlines():
            line = line.strip()
            # Skip empty lines or full-line comments
            if not line or line.startswith("#"):
                continue
                
            # Find all matching words or strings on this line
            matches = re.findall(token_specification, line)
            
            for match in matches:
                # If it's a string literal, strip the quotes and classify it
                if (match.startswith('"') and match.endswith('"')) or (match.startswith("'") and match.endswith("'")):
                    tokens.append(Token(Token.STRING, match[1:-1]))
                # Classify special keywords
                elif match == "define":
                    tokens.append(Token(Token.DEFINE, match))
                elif match == "as":
                    tokens.append(Token(Token.AS, match))
                elif match == "call":
                    tokens.append(Token(Token.CALL, match))
                elif match == "with":
                    tokens.append(Token(Token.WITH, match))
                # Otherwise, it's a variable or function name
                else:
                    tokens.append(Token(Token.IDENTIFIER, match))
                    
        return tokens
