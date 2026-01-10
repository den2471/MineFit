import rich

def concatenate_endpoint(url: str, slug: str) -> str:
    return url.replace('[id]', slug)

class pcolor:
    default = "#FFFFFF"
    success = "#68FF54"
    error = "#FF6A6A"
    disabled = "#646464"

def cprint(text: str, color: str = pcolor.default, end: str = ''):
    rich.print(f'[{color}]{text}', end=end)