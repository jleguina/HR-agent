# HR-agent

### Deployment

(DEPLOYMENT IS OFF) Agent can be found at: https://hr-agent.streamlit.app/

### Run locally

To run the agent, do the following:

    1. Install the requirements: `poetry install`
    2. Run streamlit: `poetry run streamlit run app/main.py`

### Issues

1. Slack:

   - Problem: Adding users to a Slack workspace requires an Enterprise Grid subscription. See [here](https://api.slack.com/methods/admin.users.invite).
   - Solution: instead of using the Slack API, the agent sends an invite link via email.

2. StackOne:

   - I would have liked to use StackOne for the API interactions with BambooHR. I could not authenticate with StackOne so I used the BambooHR API directly.

3. Onboarding status updates:
   - Problem: The agent executes all the onboarding steps as part of the first chat "action". Since the LLM runs in synchronous mode within Streamlit the only way to provide status updates is to pass callbacks to the agent's tools. However, Streamlit never rerenders individual components (such as the onboarding progress widget on the sidebar), but only reruns the whole script in response to every interaction. This means the state changes triggered by the callbacks didn't lead to a rerender until the LLM call had returned.
   - Impact: Unable to provide real-time updates during the onboarding process. Status updates are available only after the completion of the entire onboarding flow.
   - Solution: Incorporate asynchronous task handling with Python's concurrency mechanisms (e.g., multiprocessing, threading) or use a task queue and workers like Redis+Celery. Or just don't use Streamlit.
