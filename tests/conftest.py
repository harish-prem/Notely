from hypothesis import HealthCheck, settings

settings.register_profile(
    "notely", suppress_health_check=[HealthCheck.function_scoped_fixture]
)

# any tests executed before loading this profile will still use the
# default active profile of 100 examples.

settings.load_profile("notely")

# any tests executed after this point will use the active notely
# profile of 10 examples.
