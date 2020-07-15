
from IPython.display import display_html

def display_inline(*args, start=0, stop=10):
    html_str=''
    for df in args:
        df = df.iloc[start:stop]
        html_str+=df.to_html()
    display_html(html_str.replace('table','table style="display:inline"'), raw=True)
