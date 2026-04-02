"""
Gradio API Client for /predict endpoint

Requirements:
    python -m pip install gradio_client

Gradio App:
    http://127.0.0.1:7860
"""

from gradio_client import Client


class GradioPredictClient:
    """
    Simple client wrapper for Gradio /predict API
    """

    def __init__(self, base_url: str = "http://127.0.0.1:7860"):
        self.base_url = base_url
        self.client = Client(self.base_url)

    def predict(self, text: str) -> str:
        """
        Call the /predict endpoint.

        Args:
            text (str): Input text

        Returns:
            str: Prediction output
        """
        if not isinstance(text, str) or not text.strip():
            raise ValueError("`text` must be a non-empty string")

        return self.client.predict(
            text=text,
            api_name="/predict"
        )


def main():
    """
    Example usage
    """
    client = GradioPredictClient()

    input_text = "I am angry today!!"
    print("Sending:", input_text)

    result = client.predict(input_text)
    print("Response:", result)


if __name__ == "__main__":
    main()
