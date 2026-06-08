# TestPlus Framework Design Document

## Overview

The TestPlus framework is a distributed test automation system built on top of the AutomationMojo testbase package. It provides a comprehensive solution for executing tests across distributed environments with sophisticated configuration management, landscape integration, and result reporting capabilities.

## Architecture

### Core Components

#### 1. Test Job Management (`DistributedTestJob`)
The `DistributedTestJob` class serves as the primary orchestrator for test execution:

- **Purpose**: Manages the complete lifecycle of a test run from discovery to result reporting
- **Key Features**:
  - Configuration requirement flags (credentials, landscape, topology, runtime)
  - Multi-phase execution pipeline with clear separation of concerns
  - Integration with landscape management for distributed testing
  - Comprehensive error handling and import error tracking
  - Result recording and HTML report generation

- **Execution Phases**:
  1. **Discovery**: Test discovery and import error collection
  2. **Integration Publishing**: Configuration activation and framework attachment
  3. **Resource Collection**: Global shared resource checkout
  4. **Operations Activation**: Connectivity establishment with test landscape
  5. **Presence Establishment**: Persistent functionality setup on remote devices
  6. **Diagnostic Capture**: Pre-test diagnostic information gathering
  7. **Test Execution**: Actual test running with result recording
  8. **Post-Run Diagnostics**: Final diagnostic capture

#### 2. Test Sequencing (`DistributedTestSequencer`)
Extends the base `TestSequencer` to provide distributed testing capabilities:

- **Purpose**: Controls the flow and orchestration of distributed test execution
- **Key Features**:
  - Landscape integration for distributed environments
  - Integration coupling management
  - Environment attachment and configuration
  - Startup configuration recording

#### 3. Command Line Interface
Comprehensive CLI built with Click framework:

- **Main Command**: `testplus` - Entry point with verbosity controls
- **Testing Commands**:
  - `run` - Execute test collections with extensive configuration options
  - `query` - Discover and list available tests
  - `jobs` - Manage and execute predefined test jobs

#### 4. Configuration Management
Sophisticated configuration system supporting multiple sources:

- **Configuration Types**: Credentials, Landscape, Runtime, Topology
- **Source Options**: Files, names, and URI-based sources
- **Override System**: Command-line options override configuration files
- **Default Configurations**: Bulk configuration loading with "all" option

#### 5. Initialization System
Two-phase initialization for runtime and results:

- **Runtime Initialization** (`initialize_testplus_runtime`):
  - Application persona establishment
  - Default type factory registration
  - Home directory and logging configuration

- **Results Initialization** (`initialize_testplus_results`):
  - Static resource and template path configuration
  - Runtime variable population
  - Job profile activation

## Key Design Patterns

### 1. Factory Pattern
- `TestPlusDefaultTypeFactory` provides default implementations
- Extensible factory system for customizing job types
- Super factory pattern for type resolution

### 2. Context Manager Pattern
- `DistributedTestJob` implements context manager protocol
- Automatic resource cleanup and finalization
- Exception handling with proper cleanup

### 3. Phase-Based Execution
- Clear separation of test execution phases
- Each phase has specific responsibilities
- Early failure detection in configuration phases

### 4. Plugin Architecture
- Extension modules for customization
- Integration coupling system for external integrations
- Configurable type factories

## Configuration Architecture

### Configuration Sources
1. **Files**: Direct file paths for configuration documents
2. **Names**: Base names searched in configured paths
3. **Sources**: URI-based configuration sources
4. **Defaults**: Predefined configuration sets

### Configuration Types
- **Credentials**: Authentication and authorization data
- **Landscape**: Test environment topology and device information
- **Runtime**: Execution parameters and runtime settings
- **Topology**: Network and infrastructure configuration

### Override Hierarchy
1. Command-line options (highest priority)
2. Configuration files
3. Default configurations
4. Built-in defaults (lowest priority)

## Integration Points

### 1. Landscape Integration
- `LandscapeSingleton` for distributed environment management
- Multi-phase activation (configuration → integration → operations)
- Device connectivity and presence establishment

### 2. Result Recording
- `JsonResultRecorder` for structured result capture
- Stream and consolidated result formats
- HTML report generation with templates
- Static resource management

### 3. Diagnostic System
- Pre and post-run diagnostic capture
- Configurable diagnostic levels
- Integration with landscape for distributed diagnostics

## Entry Points and Usage

### 1. Programmatic Entry Point
```python
from ccai.testplus.entrypoints import distributed_test_entrypoint
distributed_test_entrypoint(job_type=CustomTestJob)
```

### 2. Command Line Usage
```bash
# Run tests with configuration
testplus testing run --root ./tests --includes "*.test.*" --landscape myenv

# Query available tests
testplus testing query --root ./tests

# Run specific job
testplus testing jobs run --job "mypackage.jobs@MyTestJob"
```

### 3. Test Module Integration
Test modules can include the entry point for standalone execution:
```python
if __name__ == "__main__":
    distributed_test_entrypoint()
```

## Error Handling and Diagnostics

### Import Error Management
- Comprehensive import error tracking during test discovery
- Separate recording of import failures
- Visibility into missing dependencies and syntax errors

### Diagnostic Capture
- Pre-run diagnostics for environment validation
- Post-run diagnostics for failure analysis
- Integration with distributed landscape for comprehensive diagnostics

### Result Reporting
- Multiple output formats (JSON stream, consolidated JSON, HTML)
- Static resource copying for self-contained reports
- Build and pipeline information integration

## Extensibility Points

### 1. Custom Job Types
- Inherit from `DistributedTestJob`
- Override configuration requirements
- Customize execution phases

### 2. Custom Sequencers
- Extend `DistributedTestSequencer`
- Modify test discovery and execution flow
- Add custom integration points

### 3. Custom Recorders
- Implement `ResultRecorder` interface
- Custom result formats and destinations
- Integration with external reporting systems

### 4. Factory Extensions
- Implement `TestBaseFactoryProtocol`
- Provide custom default types
- Plugin-based architecture

## Dependencies and Integration

### Core Dependencies
- `ccai.testbase` - Base testing framework
- `ccai.landscaping` - Distributed environment management
- `ccai.runtime` - Runtime configuration and variables
- `ccai.configuration` - Configuration management system

### External Integrations
- Click framework for CLI
- JSON for result serialization
- HTML templating for report generation
- File system operations for result management

## Design Principles

### 1. Separation of Concerns
- Clear separation between discovery, configuration, and execution
- Distinct phases with specific responsibilities
- Modular architecture with well-defined interfaces

### 2. Debuggability Over Performance
- Comprehensive logging and error reporting
- Detailed diagnostic information
- Clear error messages and stack traces

### 3. Readability Over Conciseness
- Descriptive variable and method names
- Comprehensive documentation
- Clear code structure and organization

### 4. Distributed-First Design
- Built for distributed testing environments
- Landscape integration as core feature
- Network-aware error handling and diagnostics

### 5. Configuration Flexibility
- Multiple configuration sources and formats
- Override capabilities at multiple levels
- Environment-specific configuration support

## Future Considerations

### Scalability
- Support for large-scale distributed testing
- Parallel test execution capabilities
- Resource optimization for distributed environments

### Integration
- Additional result format support
- External system integrations
- Cloud platform support

### Usability
- Enhanced CLI with interactive features
- Configuration validation and assistance
- Improved error messages and diagnostics

This design document reflects the current architecture of the TestPlus framework as implemented in the source code, emphasizing its distributed testing capabilities, comprehensive configuration management, and extensible design patterns.