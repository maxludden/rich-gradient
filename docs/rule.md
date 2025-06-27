![GradientRule](img/rule_example.svg)

# Rule

The 'Rule` class is based off of the rich.rule.Rule class and is used to define a rule in gradient color and variable thickness.

## Usage

```python
from rich.console import Console
from rich_gradient.rule import Rule

console = Console()
console.print(
    Rule(
        "Hello, world!",
    )
)
```

![Rule](https://raw.githubusercontent.com/maxludden/rich-gradient/3b6e2cb013eda3bcba9dbcdd14c65179d28532da/docs/img/rule_example1.svg)

## Alignment

The `Rule` class supports the same alignment options as the `Rule` class.

```python
console.print(
    Rule(
        "Hello, world! on the left",
        align="left",
    )
)
```

![Rule Alignment](https://raw.githubusercontent.com/maxludden/rich-gradient/3b6e2cb013eda3bcba9dbcdd14c65179d28532da/docs/img/rule_example2.svg)

## Thickness

The `Rule` class add the ability to determine the thickness of the rule. Valid values are `thin`, `medium`, and `thick`. Defaults to `medium`.

```python
console.print(
    Rule(
        "Hello, world! thick",
        thickness="thick"
    )
)
```

![Rule Thickness](https://raw.githubusercontent.com/maxludden/rich-gradient/3b6e2cb013eda3bcba9dbcdd14c65179d28532da/docs/img/rule_example3.svg)
