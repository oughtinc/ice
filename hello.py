from ice.recipe import recipe


async def foo():
    return "foo"

async def say_hello():
    await foo()
    return "Hello world!"


recipe.main(say_hello)