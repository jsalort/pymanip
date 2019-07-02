import pypandoc

z = pypandoc.convert("README.md", "rst", format="markdown")
with open("README.rst", "w") as outfile:
    outfile.write(z)
