import re

identifier = re.match(r'^(\w+)\-(\d+)$', 'User-10')
print(identifier.group(2))