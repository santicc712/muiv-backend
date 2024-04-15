import aiofiles


async def async_read_txt(path: str, encoding="utf-8"):
    async with aiofiles.open("data/text/{}.txt".format(path), "r", encoding=encoding) as file:
        text = await file.read()
    return text


def read_txt(path: str, encoding="utf-8"):
    with open("data/text/{}.txt".format(path), "r", encoding=encoding) as file:
        text = file.read()
    return text
