import sys
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))
from watchdog_memo_ngrok import is_public_endpoint_healthy


class WatchdogHealthTests(unittest.TestCase):
    def test_public_endpoint_unhealthy_when_err_ngrok_3200_header(self):
        self.assertFalse(
            is_public_endpoint_healthy(
                404,
                {"Ngrok-Error-Code": "ERR_NGROK_3200"},
                "offline",
            )
        )

    def test_public_endpoint_unhealthy_when_body_contains_err_ngrok_3200(self):
        self.assertFalse(
            is_public_endpoint_healthy(
                404,
                {},
                "The endpoint is offline. ERR_NGROK_3200",
            )
        )

    def test_public_endpoint_healthy_for_redirect_to_login(self):
        self.assertTrue(
            is_public_endpoint_healthy(
                302,
                {"Location": "/login?next=/"},
                "",
            )
        )


if __name__ == "__main__":
    unittest.main()
