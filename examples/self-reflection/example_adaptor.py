import typing
import weave


@weave.type()
class ExampleAdaptor:
    output_guidance: typing.Optional[str]

    @weave.op()
    def example_to_prompt(example: typing.Any) -> typing.Any:
        ...
