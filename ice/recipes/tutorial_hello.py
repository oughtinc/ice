from ice.recipe import Recipe


class HelloWorld(Recipe):
    async def run(self):
        return "Hello world!"
