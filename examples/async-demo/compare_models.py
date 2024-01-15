import weave
import openai
import asyncio
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.live import Live

# Create a console object
console = Console()

# Define the layout
layout = Layout()

# Split the layout into two side-by-side (horizontal) sections
layout.split_row(
    Layout(name="left"),  # Width of 30 for the left panel
    Layout(name="right"),  # Remaining space for the right panel
)

# Initialize left and right panels
layout["left"].update(Panel(""))
layout["right"].update(Panel(""))

weave.init("wf-oai-stream1")


@weave.op()
async def predict(message: str, model: str):
    client = openai.AsyncClient()
    return await client.chat.completions.create(
        model=model,
        stream=True,
        messages=[{"role": "user", "content": message}],
    )


async def do_preds(message, model, layout):
    response_message = ""
    async for chunk in await predict(message, model):
        content = chunk.choices[0].delta.content
        if content is not None:
            response_message += content
            size = console.size
            # This is jank, we actually want to know how many lines to
            # render and deal with word wrap. I can't figure out how to get
            # rich panels to handle this for us. So this is a heuristic
            # for how much we can display. But it makes the the top paragraph
            # stream out in a weird way.
            avail_chars = (size.height - 10) * ((size.width // 2) - 5)
            show_message = response_message
            if len(show_message) > avail_chars:
                show_message = "..." + show_message[-(avail_chars - 4) :]
            layout.update(Panel(show_message))
    return response_message


async def main():
    with Live(layout, console=console, refresh_per_second=10):
        message = "Please tell me a very short story about a robot who is a judge on a reality tv show"
        left = do_preds(message, "gpt-3.5-turbo", layout["left"])
        right = do_preds(message, "gpt-4", layout["right"])
        await asyncio.gather(left, right)


if __name__ == "__main__":
    asyncio.run(main())
