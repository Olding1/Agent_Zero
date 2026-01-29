import pkgutil
import langchain_community.tools
import os

print("Scanning langchain_community.tools...")
package = langchain_community.tools
prefix = package.__name__ + "."

for _, name, is_pkg in pkgutil.iter_modules(package.__path__, prefix):
    print(f"{'[PKG]' if is_pkg else '[MOD]'} {name}")
