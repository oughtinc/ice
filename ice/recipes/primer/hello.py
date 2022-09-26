from ice.recipe import recipe


async def say_hello():
    return "Hello world!"


recipe.main(say_hello)
