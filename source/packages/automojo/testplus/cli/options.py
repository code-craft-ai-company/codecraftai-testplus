"""
    .. module:: options
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Reusable option groups for the TestPlus CLI.
"""

from typing import Type

from automojo.arcli.decorators import option
from automojo.arcli.model.fields.optionfield import OptionMode
from automojo.arcli.model.parameters.booleanparameter import BooleanParameter
from automojo.arcli.model.parameters.stringparameter import StringParameter
from automojo.arcli.model.parameters.validators import Choice

from automojo.xmodules.xlogging.levels import LOG_LEVEL_NAMES

from automojo.testplus.cli.cmdtree.testing.constants import (
    CONFIGURATION_CHOICES,
    HELP_ROOT,
    HELP_EXCLUDES,
    HELP_INCLUDES,
    HELP_OUTPUT,
    HELP_START,
    HELP_BRANCH,
    HELP_BUILD,
    HELP_FLAVOR,
    HELP_JOB,
    HELP_FILTER,
    HELP_JOB_ID,
    HELP_JOB_INITIATOR,
    HELP_JOB_LABEL,
    HELP_JOB_NAME,
    HELP_JOB_OWNER,
    HELP_RUNID,
    HELP_CONSOLE_LOG_LEVEL,
    HELP_FILE_LOG_LEVEL,
    HELP_DEBUG,
    HELP_DEBUGGER,
    HELP_BREAKPOINT,
    HELP_PRERUN_DIAGNOSTIC,
    HELP_POSTRUN_DIAGNOSTIC,
    HELP_INCLUDE_MARKER_EXP,
    HELP_EXCLUDE_MARKER_EXP,
    HELP_CONFIG_NAME,
    HELP_CREDENTIAL,
    HELP_CREDENTIAL_NAMES,
    HELP_CREDENTIAL_SOURCES,
    HELP_DEFAULT_CONFIGS,
    HELP_LANDSCAPE,
    HELP_LANDSCAPE_NAMES,
    HELP_LANDSCAPE_SOURCES,
    HELP_RUNTIME,
    HELP_RUNTIME_NAMES,
    HELP_RUNTIME_SOURCES,
    HELP_TOPOLOGY,
    HELP_TOPOLOGY_NAMES,
    HELP_TOPOLOGY_SOURCES,
)

def with_job_identity_options(f):
    f = option("--job-id", default=None, required=False, help=HELP_JOB_ID, group="Job Identity")(f)
    f = option("--job-initiator", default=None, required=False, help=HELP_JOB_INITIATOR, group="Job Identity")(f)
    f = option("--job-label", default=None, required=False, help=HELP_JOB_LABEL, group="Job Identity")(f)
    f = option("--job-name", default=None, required=False, help=HELP_JOB_NAME, group="Job Identity")(f)
    f = option("--job-owner", default=None, required=False, help=HELP_JOB_OWNER, group="Job Identity")(f)
    return f

def with_configuration_options(f):
    f = option("--default-configs", "default_configs", mode=OptionMode.Multiple, default=None, required=False, ptype=Choice(CONFIGURATION_CHOICES), help=HELP_DEFAULT_CONFIGS, group="Configuration")(f)
    f = option("--config-name", "config_name", default=None, required=False, help=HELP_CONFIG_NAME, group="Configuration")(f)

    f = option("--credential", "credential_files", mode=OptionMode.Multiple, default=None, required=False, help=HELP_CREDENTIAL, group="Configuration")(f)
    f = option("--credential-name", "credential_names", mode=OptionMode.Multiple, default=None, required=False, help=HELP_CREDENTIAL_NAMES, group="Configuration")(f)
    f = option("--credential-source", "credential_sources", mode=OptionMode.Multiple, default=None, required=False, help=HELP_CREDENTIAL_SOURCES, group="Configuration")(f)

    f = option("--landscape", "landscape_files", mode=OptionMode.Multiple, default=None, required=False, help=HELP_LANDSCAPE, group="Configuration")(f)
    f = option("--landscape-name", "landscape_names", mode=OptionMode.Multiple, default=None, required=False, help=HELP_LANDSCAPE_NAMES, group="Configuration")(f)
    f = option("--landscape-source", "landscape_sources", mode=OptionMode.Multiple, default=None, required=False, help=HELP_LANDSCAPE_SOURCES, group="Configuration")(f)

    f = option("--runtime", "runtime_files", mode=OptionMode.Multiple, default=None, required=False, help=HELP_RUNTIME, group="Configuration")(f)
    f = option("--runtime-name", "runtime_names", mode=OptionMode.Multiple, default=None, required=False, help=HELP_RUNTIME_NAMES, group="Configuration")(f)
    f = option("--runtime-source", "runtime_sources", mode=OptionMode.Multiple, default=None, required=False, help=HELP_RUNTIME_SOURCES, group="Configuration")(f)

    f = option("--topology", "topology_files", mode=OptionMode.Multiple, default=None, required=False, help=HELP_TOPOLOGY, group="Configuration")(f)
    f = option("--topology-name", "topology_names", mode=OptionMode.Multiple, default=None, required=False, help=HELP_TOPOLOGY_NAMES, group="Configuration")(f)
    f = option("--topology-source", "topology_sources", mode=OptionMode.Multiple, default=None, required=False, help=HELP_TOPOLOGY_SOURCES, group="Configuration")(f)
    return f

def with_logging_options(f):
    f = option("--console-level", default=None, required=False, ptype=Choice(LOG_LEVEL_NAMES, case_sensitive=False), help=HELP_CONSOLE_LOG_LEVEL, group="Logging")(f)
    f = option("--logfile-level", default=None, required=False, ptype=Choice(LOG_LEVEL_NAMES, case_sensitive=False), help=HELP_FILE_LOG_LEVEL, group="Logging")(f)
    return f

def with_debugging_options(f):
    f = option("--debugger", default=None, required=False, ptype=Choice(['pdb', 'debugpy']), help=HELP_DEBUGGER, group="Debugging")(f)
    f = option("--breakpoint", "breakpoints", default=None, required=False, mode=OptionMode.Multiple, ptype=Choice(['test-discovery', 'testrun-start']), help=HELP_BREAKPOINT, group="Debugging")(f)
    return f

def with_diagnostic_options(f):
    f = option("--prerun-diagnostic", ptype=BooleanParameter, default=False, required=False, help=HELP_PRERUN_DIAGNOSTIC, group="Diagnostics")(f)
    f = option("--postrun-diagnostic", ptype=BooleanParameter, default=False, required=False, help=HELP_POSTRUN_DIAGNOSTIC, group="Diagnostics")(f)
    return f

def with_filtering_options(f):
    f = option("--excludes", "-x", mode=OptionMode.Multiple, required=False, help=HELP_EXCLUDES, group="Filtering")(f)
    f = option("--includes", "-i", mode=OptionMode.Multiple, help=HELP_INCLUDES, group="Filtering")(f)
    f = option("--include-marker-exp", required=False, mode=OptionMode.Multiple, help=HELP_INCLUDE_MARKER_EXP, group="Filtering")(f)
    f = option("--exclude-marker-exp", required=False, mode=OptionMode.Multiple, help=HELP_EXCLUDE_MARKER_EXP, group="Filtering")(f)
    return f

def with_common_build_options(f):
    f = option("--branch", default=None, required=False, help=HELP_BRANCH, group="Build Info")(f)
    f = option("--build", default=None, required=False, help=HELP_BUILD, group="Build Info")(f)
    f = option("--flavor", default=None, required=False, help=HELP_FLAVOR, group="Build Info")(f)
    return f

def with_run_context_options(f):
    f = option("--root", default=None, required=False, help=HELP_ROOT, group="Run Context")(f)
    f = option("--output", "-o", default=None, required=False, help=HELP_OUTPUT, group="Run Context")(f)
    f = option("--start", default=None, required=False, help=HELP_START, group="Run Context")(f)
    f = option("--runid", default=None, required=False, help=HELP_RUNID, group="Run Context")(f)
    f = with_common_build_options(f)
    return f
