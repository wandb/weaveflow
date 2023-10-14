# Weaveflow Docs

Weaveflow is a prototype of our next generation AI tooling.

The features are built in to a branch of our weave library.

## Getting started

See the [root readme](/README.md) in this repo for setup instructions.

Try the [text extraction example](/examples/text-extract/)

## Overview

Weaveflow is built on a few very simple concepts to enable AI workflows...

## API

### weave.init

Start tracking any called ops, by logging their code, inputs and outputs and metadata.

```
weave.init(f'<entity>/<project>')

```

### weave.publish

Publish and version data on top of W&B Artifacts.

```
weave.publish(<object>, <name>)
```

You can publish the following python types:

- bool
- int
- float
- str
- dict
- list (but it's recommended to wrap large lists with weave.WeaveList. This will soon be automatic)
- objects from classes decorated with @weave.type()

### weave.ref (and ref.get())

Get published object versions back into Python.

You need to pass in a well-formed weave ref. The UI will present this code soon.

```
ref('wandb-artifact:///shawn/text-extract26/dataset:a12581bahasdf/obj').get()
```

### @weave.op decorator

Keep track of a function with Weave.

Weave will:

- save and version the function's code
- make the function relocatable so it can be called from the UI, served in production, and executed on other systems
- log executions of the function, it's inputs and outputs, and ancestors and descendents

You have to first call weave.init() for the above to happen!

weave.op() currently requires that you annotate the inputs and outputs using Python types.

```
def predict_name(doc: str) -> typing.Any:
    match = re.search(r'name.*is ([^.]*)(\.|\n)', doc)
    return match.group(1) if match else None

def predict_shares(doc: str) -> typing.Any:
    match = re.search(r'[Ss]hares.*?([\d,]+)', doc)
    return match.group(1).replace(',', '') if match else None

@weave.op()
def predict(doc: str) -> typing.Any:
    return {
        'name': predict_name(doc),
        'shares': predict_shares(doc)
    }
```

### @weave.type decorator

Create a class that can be published.

```
@weave.type()
class Prompt:
    text: str

@weave.type()
class OpenAIChatModel(weave.Model):
    model_name: str
    prompt: Prompt

    @weave.op()
    def predict(self, doc: str) -> typing.Any:
        import json
        from weave.monitoring import openai
        response = openai.ChatCompletion.create(
            model=self.model_name,
            messages=[
                {'role': 'user',
                 'content': self.prompt.text.format(doc=doc)}])
        result = response['choices'][0]['message']['content']
        parsed = json.loads(result)
        return {
            'name': parsed['name'],
            'shares': int(parsed['shares'])
        }
```

## Builtin base types

Dataset

...

Model

...

## Integrations

openai

...
