import pytest
import subprocess
from gittf.workflow import Workflow, Steps, Step
from pydantic import ValidationError


def test_worklow_handles_unexpected_keys():
    with pytest.raises(ValidationError):
        Workflow.parse_obj({"foo": "bar"})


def test_workflow_steps_parses_steps_configuration():
    Steps.parse_obj({'steps': [
        {'run': 'my-custom-command arg1 arg2'},
        'init',
        {'plan': {
            'extra_args': ['-lock', 'false']}
         },
        {'run': 'my-custom-command arg1 arg2'}
    ]})

    Steps.parse_obj({'steps': ['init']})


def test_workflow_step_handles_unexpected_step_configurations():
    with pytest.raises(ValueError):
        Step.parse_obj('foo').command

    with pytest.raises(ValueError):
        Step.parse_obj([{'foo': 'bar'}]).command


def test_run_step_command():
    step = Step.parse_obj({'run': 'echo bar'})
    assert step.command == 'echo bar'


def test_init_with_extra_steps():
    step = Step.parse_obj({'init': {'extra_args': ['-refresh=false']}})
    assert step.command == 'terraform init -no-color -input=false -refresh=false && terraform workspace select $WORKSPACE'


def test_run_command_executed_with_all_environment_variables():
    pass


def test_terraform_command_with_no_args():
    step = Step.parse_obj('plan')
    assert step.command == 'terraform plan -no-color -input=false -out=plan | grep -v Refreshing'


def test_terraform_command_with_extra_args():
    pass


def test_env_command():
    pass


def test_multienv_command():
    pass


def test_full_workflow():
    w = Workflow.parse_obj(
        {'plan': {'steps': [
            {'run': 'my-first-command arg1 arg2'},
            'init',
            {'plan': {
                'extra_args': ['-lock', 'false']}
             },
            {'run': 'my-custom-command arg1 arg2'}
        ]}
        })

    commands = w.get_commands('plan')

    assert 'my-first-command arg1 arg2' in commands
    assert 'terraform init -no-color -input=false' in commands

def test_static_env_value():
    step = Step.parse_obj({'env': {'name': 'FOO', 'value': 'BAR'}})
    assert step.command == 'export FOO=BAR'

def test_dynamic_env_value():
    step = Step.parse_obj({'env': {'name': 'FOO', 'command': 'echo BAZ'}})
    assert step.command == 'export FOO=$(echo BAZ)'


def test_env_variables_are_added_to_subsequent_steps():
    w = Workflow.parse_obj(
        {'plan': {'steps': [
            {'env': {'name': 'FOO', 'value': 'BAR'}},
            {'run': 'echo $FOO'},
        ]}
    })
    
    command = w.get_commands('plan')

    proc = subprocess.run(command, shell=True, check=True, capture_output=True)
    assert proc.stdout.decode('utf-8') == 'BAR\n'

def test_default_workflow():
    w = Workflow.parse_obj({})

    plan_commands = w.get_commands('plan')
    apply_commands = w.get_commands('apply')
    assert 'terraform init' in plan_commands
    assert 'terraform init' in apply_commands
    assert 'terraform plan' in plan_commands
    assert 'terraform apply' in apply_commands