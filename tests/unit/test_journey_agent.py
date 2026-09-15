def test_changed_maps_a_known_file_to_its_intents():
    from evals.journey_eval import intents_for_changes

    assert intents_for_changes(["app/tools/catalog.py"]) == "cart,discovery,negative"
    assert intents_for_changes(["app/tools/reviews.py"]) == "reviews"


def test_changed_runs_everything_for_a_prompt_or_unmapped_change():
    """Conservative by design: guessing which intents a prompt change affects is how
    a regression slips through."""
    from evals.journey_eval import intents_for_changes

    assert intents_for_changes(["config/prompts/journey.md"]) == ""
    assert intents_for_changes(["app/something/new.py"]) == ""
    assert intents_for_changes([]) == ""


def test_changed_unions_the_intents_of_several_files():
    from evals.journey_eval import intents_for_changes

    assert intents_for_changes(["app/tools/reviews.py", "app/tools/catalog.py"]) == (
        "cart,discovery,negative,reviews"
    )
