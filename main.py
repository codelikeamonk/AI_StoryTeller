# import os
# import openai

"""
Before submitting the assignment, describe here in a few sentences what you would have built next if you spent 2 more hours on this project:

I would add a small quantitative benchmarking script that runs a fixed set of 10-20 representative story requests through the system using
different prompt variants, such as baseline versus revised storyteller prompts. For every run, log the judge's scores on age-appropriateness, safety
engagement, structure, etc into a CSV and compute an aggregate “quality score” per prompt version. That would make it super easy to compare prompt
changes objectively, identify regressions, and iterate based on measured improvements rather than by subjective judgment.
"""
from pipeline import generate_story_with_judge, revise_story_with_user_feedback, format_judge_debug

def main():
    user_input = input("What kind of story do you want to hear? ").strip()
    if not user_input:
        user_input = "A story about a girl named Alice and her best friend Bob, who happens to be a cat."

    story, judge_history = generate_story_with_judge(
        user_input,
        max_rounds=3,
        length="medium",
        style="calm",
    )

    print("\n" + "-" * 100)
    print("STORY")
    print("-" * 100 + "\n")
    print(story)

    # print("\n" + "-" * 100)
    # print("JUDGE SUMMARY (debug)")
    # print("-" * 100)
    # print(format_judge_debug(judge_history))

    # Feedback loop
    for i in range(3):
        feedback = input(
            "\nAny changes? (e.g., 'shorter', 'funnier', 'more about Bob')\n"
            "Press Enter to accept the story and finish: "
        ).strip()

        # Explicit accept path
        if feedback == "":
            print("\nStory accepted.")
            break

        story, fb_judge_history = revise_story_with_user_feedback(
            user_input,
            story,
            feedback,
            max_rounds=2,
        )

        print("\n" + "=" * 60)
        print(f"UPDATED STORY (edit {i + 1})")
        print("=" * 60 + "\n")
        print(story)

        # print("\n" + "=" * 60)
        # print("JUDGE SUMMARY (debug)")
        # print("=" * 60)
        # print(format_judge_debug(fb_judge_history))

    print("\nGoodnight, Sweet Dreams!")


if __name__ == "__main__":
    main()
