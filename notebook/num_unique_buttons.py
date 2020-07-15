
from ipywidgets import Dropdown, Output
from IPython.display import display, Markdown, HTML, clear_output

default = '--'
options=['--', 'domestic declarations', 'international declarations',\
            'prepaid travel costs', 'request for payment', 'travel permitions']

dropdown = Dropdown(options=options, value=default,
                   description='Unique cat')

def _display(arg):
    HTML("""
        <style>
        .output {
            display: flex;
            align-items: center;
            text-align: right;
        }
        </style>
        """)
    display(arg)
    

def dropdown_eventhandler(option):
    output
    if option.new == default:
        clear_output()
        _display(dropdown)
    else:
        clear_output()
        _display(dropdown)
        _display(Markdown(f'{option.new}.md'))        
        

dropdown.observe(dropdown_eventhandler, names='value')
_display(dropdown)
