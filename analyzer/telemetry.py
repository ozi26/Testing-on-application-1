# =============================================================================
# TELEMETRY MODULE
# This module contains functions for setting up OpenTelemetry tracing.
# OpenTelemetry allows us to trace what happens when tests run, so we
# can see which services and configurations are used.
# =============================================================================

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter


# Global variables to store the tracer and exporter
# We use these to access the tracing system from other modules
_tracer = None
_span_exporter = None


def configure_tracing():
    """
    Set up OpenTelemetry tracing for the application.
    
    This function creates a tracer provider, sets up an in-memory
    span exporter (so we can inspect spans after tests run), and
    registers the tracer globally.
    
    Returns:
        The span exporter object, which can be used to access
        the recorded spans.
    
    Example:
        exporter = configure_tracing()
        # Now tracing is active
        # After running tests, we can inspect exporter.get_finished_spans()
    """
    global _tracer, _span_exporter
    
    # Create an in-memory span exporter
    # This stores spans in memory so we can inspect them after tests run
    _span_exporter = InMemorySpanExporter()
    
    # Create a tracer provider
    # This is responsible for creating tracers and managing span processors
    provider = TracerProvider()
    
    # Create a simple span processor that sends spans to our exporter
    # SimpleSpanProcessor processes spans as they are finished
    processor = SimpleSpanProcessor(_span_exporter)
    
    # Add the processor to the provider
    provider.add_span_processor(processor)
    
    # Set the global tracer provider
    # This makes the provider available to all tracers created afterward
    trace.set_tracer_provider(provider)
    
    # Create a tracer with a descriptive name
    # Tracers are used to create spans
    _tracer = trace.get_tracer("test-impact-analyzer")
    
    # Return the exporter so callers can access recorded spans
    return _span_exporter


def get_tracer():
    """
    Get the global tracer instance.
    
    Returns:
        The tracer object, or None if tracing hasn't been configured yet.
    
    Example:
        tracer = get_tracer()
        with tracer.start_as_current_span("my-operation"):
            # Code here will be traced
            pass
    """
    return _tracer


def get_span_exporter():
    """
    Get the global span exporter instance.
    
    Returns:
        The span exporter object, or None if tracing hasn't been configured.
    
    Example:
        exporter = get_span_exporter()
        spans = exporter.get_finished_spans()
        # spans contains all the recorded spans
    """
    return _span_exporter


def reset_tracing():
    """
    Reset the tracing system, clearing all recorded spans.
    
    This is useful between test runs to ensure we don't mix
    spans from different test executions.
    
    Example:
        reset_tracing()
        # Now the exporter has no spans
    """
    global _span_exporter
    
    # If we have an exporter, clear its recorded spans
    if _span_exporter is not None:
        _span_exporter.clear()