from pydantic import BaseModel, Extra
from typing import List, Union, Optional

class Step(BaseModel):
    __root__: Union[dict, str]

    @property
    def command(self):
        value = self.__root__
        key = None
        command = None
        if isinstance(value, str):
            if value == 'init':
                command = f"terraform init -no-color -input=false && terraform workspace select $WORKSPACE"
            elif value == 'plan':
                command = f"terraform plan -no-color -input=false -out=plan | grep -v Refreshing"
            elif value == 'apply':
                command = f"terraform apply -no-color -input=false plan | grep -v Refreshing"
            else:
                raise ValueError('Step can only be: init, plan, apply')

        if isinstance(value, dict):
            key = list(value.keys())[0]
            if key in ['init', 'plan', 'apply']:
                assert 'extra_args' in value[key]

            if key == 'init':
                extra_args = " ".join(value[key]['extra_args'])
                command = f"terraform init -no-color -input=false {extra_args} && terraform workspace select $WORKSPACE"
            elif key == 'plan':
                extra_args = " ".join(value[key]['extra_args'])
                command = f"terraform plan -no-color -input=false -out=plan {extra_args} | grep -v Refreshing"
            elif key == 'apply':
                extra_args = " ".join(value[key]['extra_args'])
                command = f"terraform apply -no-color -input=false {extra_args} plan | grep -v Refreshing"
            elif key == 'run':
                command = f"{value[key]}"
            elif key == 'env':
                if 'value' in value[key]:
                    command = f"export {value[key]['name']}={value[key]['value']}"
                elif 'command' in value[key]:
                    command = f"export {value[key]['name']}=$({value[key]['command']})"
            else:
                raise ValueError('Step can only be: init, plan, apply', 'run')
        
        return command

class Steps(BaseModel):
    steps: List[Step]

    class Config:
        extra = Extra.forbid

class Workflow(BaseModel):
    plan: Optional[Steps] = Steps(steps=[ Step.parse_obj('init'), Step.parse_obj('plan') ])
    apply: Optional[Steps] = Steps(steps=[ Step.parse_obj('init') , Step.parse_obj('apply') ])

    class Config:
        extra = Extra.forbid

    def get_commands(self, stage):
        assert stage in ['plan', 'apply'], f"Invalid stage: {stage}"

        return '&& '.join([ step.command for step in getattr(self, stage).steps ])