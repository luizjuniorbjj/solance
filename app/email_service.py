"""
SoulHaven - Servico de Email
Usa Resend para envio de emails transacionais
"""

import httpx
from typing import Optional
from app.config import RESEND_API_KEY, EMAIL_FROM, EMAIL_REPLY_TO, APP_URL, APP_NAME


class EmailService:
    """Servico de envio de emails via Resend"""

    def __init__(self):
        self.api_key = RESEND_API_KEY
        self.base_url = "https://api.resend.com"
        self.from_email = EMAIL_FROM
        self.reply_to = EMAIL_REPLY_TO

    async def send_email(
        self,
        to: str,
        subject: str,
        html: str,
        text: Optional[str] = None
    ) -> bool:
        """Envia um email via Resend API"""
        if not self.api_key:
            print("[EMAIL] API Key nao configurada - email nao enviado")
            return False

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/emails",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "from": self.from_email,
                        "to": [to],
                        "subject": subject,
                        "html": html,
                        "text": text or "",
                        "reply_to": self.reply_to
                    }
                )

                if response.status_code == 200:
                    print(f"[EMAIL] Enviado com sucesso para {to}")
                    return True
                else:
                    print(f"[EMAIL] Erro ao enviar: {response.status_code} - {response.text}")
                    return False

        except Exception as e:
            print(f"[EMAIL] Excecao ao enviar: {e}")
            return False

    # ============================================
    # TEMPLATES DE EMAIL
    # ============================================

    def _base_template(self, content: str) -> str:
        """Template base para todos os emails"""
        # Logo embutido em base64 para garantir exibicao em todos os clientes de email
        logo_base64 = "iVBORw0KGgoAAAANSUhEUgAAARgAAAC6CAIAAAD6T8WKAABP1ElEQVR42tW9d7htVXU2Pt4511q7nLNPv517gQuX3juCYsECUoMalCCgicEkX0z5fSmfMXmSGAs20M8YRY1dAY0NFURR6Sgo7Upvt7dzT9v77LLWnOP7Y5+yyypzlX0uv/NceG7ZZa255hhzlHe8L1asOpaIiHj+P+b5PxJh7r+AH27/X/tLEfLGrg8J+23bJ7PBJ3ZeNc//sfkbbvscEPxvkdn3QtF9TYt/aLsBDn33wtu46zfz/y1+RNubAZ9l4Mgl8H8lB74JXWsXvhm6l3t+C3TcBwcsQfRD7VpLDrgi7v4mzF8PyPdiYHZb3PqoWj/TYmJ0fi6HbncjmyA0N6K/KXLn9vH9mpabZIrxw+0fhJY/ss8OZDRXoM0WOOjOFy+Koy88YCP4vLL1N2C/61h4fMzh64/FJcDcH5hMnii33VTLJgX7XQ6Rjw/i1vcy+7jdzo9gs63GwV8VeGto22ldd9hq3wiyKO7attyywwHm5va0Op7Z3O7nxevmSFfBwTcDDl0qNrAQhHu9eOYd8II5X9JxApg6Xopn5/E8Qoi1BNvD/As46BiI/Ea0btUQy+WW85PaPRHQvWE5mYdOs8joMhj4XAz7+vzQpeM5D9/8SIuZfR5Kd1zG5m42+HCIvQRBMQkQEmfGjC2TXydH/yOysp/43iGViXOcl6Lr2+DnlnrkbqJvAjEfNMe61KYtWUY3GBRNcLKdkv0j9fV1HJjjcUdSEudSOJ6JZroQ++R7kz4i7kxnKDQ7e+msHhv9+1zsOr8XrDYjgV92z704cCmpefgYCYedvm1ekhcfKbenXzBOdhb8SoQ5IebzgoEba7nWl6hNRSSWAeEDB2RcXccZQmoLrW9n36w9fNWiDisOtsq5HCk4HAmoG8VfUvibBwIKayY2Gjsa8w14F+4PnSElRzm3jmM63jHF/kYLY1ffO0tiNrbVZKcKJ3+mzF3rzJ0JW6RXjR1QsH91qK0UbAUGfX52HTe6aK/2AP51qOBSbXqrjX30w7jAleSYiir68r4O9JjNPp2TmhKHOgjEv3GEtU2iw5ksIi0mIhH4Txz9VzEdDwcnW4T0+yKbIJNNP4uDHhJznGpK9Ld0/EqWEZvusCQFjWBvw9z5mrBdhEQB/3xc1/xl6MiaW5HjuImIH6t3cTKiQ+XuFUR8X5B5YM+pT0Lm4E5LhnfHxIhqmLeaXqzkaqG6a5y7LvRM2LiEnPh5tjWK2+8LMC5Z8mKq7Jtl+O5P/zuy4m7dlKYV0vnILFrLNurhpJ4z6lrQEvEycYI9hZhpBpuVNMJfn1GXAMH5auA+8b0wxI6fQxotydfAMqgNZHgsBZXaOOLGl7hWGvdpIKEnWHCEnRAEThb9sKEPnnfhbNasxtL402TpXEvXChk1ezkAYhZ2Zls9jZ8QtiXA4aEf9z6cCyl9Z4da6HoOgabltyaBVoS0IAGOWTGaSz8QaH6gDJPDKA/GBqXX+ICOoPRv0ZsEPSArqGaHdq/ZWn9D2r4Qor08p3NoHKePwzHRkmEfjoDTlTuq6gj3L/APd2C4I9nsLEUyrwOEIT7ZLI7iXpxb3J6UZpi1hIUKTAQSwcjD7iDE/954vj7TVVgKOZS555163ldvX1godBkgx+5BI6hyGlXmRG+XqMWuEbPoyv4JIfscmEjV86Gsc2VOULXjYMh/CMCTu3qLnHErERm1lTg2gtPvgAk/vJANjAOBgRmCYlCkDVBhkJnOI0U6vg2xq/N+bcqQmmEkhpp6cyiF/4igvcb+59LclXG0jbJB5YDTeg6YhXA9Pp1A6DrWQX7tjmxgkl2xQHTZAJl4LQQvP2fzlT53l3JD9B4YiR73kdJuVXMoG3oP/DMFxhnVKxCz1JZNjIY48L4MQgXubbgROhbVbUvcu83RHKMIhxoi7Nzv5bGJlzB2GjEyUSRxEtlgXcO+lnu3fsxxPwipGh4InplET3od/l8mIvPChSpCBnuh16csegCxjJeJwuRJc5r+biaL2xUBLUBsQj6IF/dDYLicJU4rxVnUXd1BQpdj+horwImgu0LMMcNN7BMAc2Blsatr15MDta0igZA9GTcp5yWAS6Flw7EZgCi+S0fSpk5nkyhtLQftJATRLZHW4XufYgNzsLNCFCIzsqWPWGMqmVULYPbv2GfoWE43PJx5e5q70GWIg6dNk9zDHDfORklq69QWZ1Fs8h+0peDyN4JQe34zIe1F2CB+gYyCcaREVSDj7ceGuVPzUPInWorgJEFPcDXGC49QEEP4RkPMUXVjvB3M3QEiIcicqTeykoH7uxvuSFCAQqKXpQwLuavit5RDvhxjWiCod7MvRpJjWARn6PsDqMDaMTuxgdBZ2E9nimnNj9uxL6FBxgUEZFdA4UxtKS1HS6zU6SVflox/8HNPy0XIBjSY4ZUhsI8UOGfYDd9OXAmJd8FsgjbYtz/oMdi8Lbudh6ghELOZ1rkkTjVpn3Qe+SXxwOf/ymoB/gS1kfwJd5A08UjezOCkDjjDiAiRpe3YsVzYUENn4jIPD0co653xHkdkGoGeR5RBQ3X8khraCFrd+UsWbBaLtMAHkfoswjyIOF0LhQ2/J0W5AgEQCn9YUMApbUqCiVDaCPbpP8HvIsNrarEuDeFA9cwrjQiiXKaXEvgGocWGoEyRu9I79vWz3LOpueipFKQ7oTkB5gy9OAHRwhLml2GHXiviQ1TaecmCSmTBvfjWJkIXPXHa/QHu3LtIFNdxdvFJAKXhHESITZs7HTOt7cxyyU0J6fFmHBPWQPF4JJKDIJNkdAigus7GP6WHRhjtabPwHSGcTG2DW4g3ARmxHEEldiDaSgN9ksXJsYuc4IEjjQsHJbrH0MU0m0VdABZmcrfhDAS81GlfwjTRx3sasi6gw0I4E+RuSALmhwtFFh5r8cazQn/zEpVL0gQMSJkKI7N4tRP113a8IwwQ7JOxIUhDpjfFNTYn5DPFm8Og3mGKi/Wdx0dmfaXApbSQZf8Ccb09x4kA9kk5u4tFrUd5MEdz6oZFlcFbBfuUmx1hzBXwqQz72h6nzoNDyMPICM8TDEXwRzYkDS3QPkLLCWPrpYK9p9hwHCNii/elXaEypyYLCbM8zMvZgCl7MY5sB0dgPKbBgaWgSJ5FzhYiFLfujsiNjXS8xAiPyxGnI8lLgSLgfQFHCCds8uWshBl2LfasvvHzTnD3nMH6IB0jB4wMiZPrDYB6oJXQ8WkwmRvLhJgvZLyoXQ8v6y47Z3CaorWXCoMpUe512gsjNamulyI4zOZIrHDQLEJoFMcJC7aC0yKXkiGtMp2kN25Hpt/VHccj97TMEtRsDXwGCMvQKWlztceQ8/n9AATfeNx15sAjcK4XhJBRZzaRvfMnP1mKXZGGAcOofo50FsixeGoMHjHSXyR6ke9xBItL9rzNIXI6hiKLSGvQnCXW29eQEDz+Mo+CQW+eeSyIEBuZj+HFdkCHYKDZ6lOEjxlq+1bREXFoI/biI+6D4s7HMf8bZIPU5g6r4RbHz/67Av5pCYyfaycHZUeBjuPxk8KMjgs+OxttKek+wD0hDgYBkWS+5nQ3vgczJ63HBLWgAmM2+L114aVhOwARDQZK8petO9MEHo7QU4DTw6wRXNgAukJbNrEZA0iPiX8WZkUJ3reDCGxwNMUWQIoZdJuTHGexJAjtHPhoJiVIbeOFtzA5BpKNbSdaVyR46sGRHmdDEBkZ28MAYmjO4tHm9hE+bMltO5mDR4uTrGr8yJlDBap67178r5ijBEvY70M44iAOY8PMQBiu7QRZWFWmMK3UCMwe+ziWzj2UIPliAx8qDIV5EN2gMUFMcRLRKd5X8vLZql2Y+G322+V+MvfRpQBEORdO4EnaAVPomiVBmjOEo3M5TqpM6w8fQuxefOBNWVn3CTmgtcwheg4wY3/6/58VobMYxZG3y+GOEtmr5/pdNNraZRHbDT78zBlXIrmtN2Zm/BwJ8DOvKUSTVote4LO6ptAihp2yYDXml9BUeeyIEZ2mw2xaEFgIZ/wOe07VOYsavvQvmKI3mK1W0QAgCysyOuwNZtOax7JlyCCbjCcNwZ2s6DMmjO0X7UL27ONdODmiJlWbnv2RMhz5pNlnxF9IMKO5d5RmDi+7LMjRxyNe4uTkI5mCrBCdH/qMmyBoMjL06zMfzbTMwyYkLA2ZEIulkv3OEs8KMubtD+SE6XDVHA52Z78TG2QJNFyeKnuWBSZoRX154TiCmbRm5tDBPXDiYf15JBGiVVWYMpVMQBac4XNKzLzkPA+WeQLCPRwL7c1twlj5D6ZJNptgLFJwDQtAgGZrerLurlxuvfGs0Te9ZqReVTffNXn/xvKm7Z6U6C9IZq00x1N2ig4AukHWHJefI0xVOnh6EcYz2guzsQjrHDAocWkifPewH/0wiBhjK45EjLIFR5PgpOGqZxMduhREMwmLFkCM2pCZF2AfE5ICs1VVrrmHr++74o3LL37F6EEriyBohvL09qn6zx6Y+NZPd9/36Izn0UCfRSCldYyaAyLtJ+QpgxKoUbDhTEenf2SDmlskFwdHWAmC25KBOudB3X8sW3FUSixgK50Sp0RnJTMkDj6ukC3uO67iClNIztLyVVIK1+XpijrykMKfXLz8kpcvWzmUr7tWrQFpg0Beg6TgQo5rbv3Oh3d97ru7fnb/tNYo9UnWrJmImsmUwTRqFLaNDcbJQpYsMJGLVmcJtiIjRWqYa8wgOV3PUhhSqC0h4WBxdGDH5oRSiPBV0RaIqPiS2woIwTQG841kSNDkjB4dFu+6cPTqi/dbMdQ3PQtNIteXh3QgNASpBpRWSmlSqpgjtzF7+4MT//emzb96cMqxZDEvPKUZIMPJ7jArIjI2JF+KkuQszTHnnQzsnDnTyQ+EYJRiGVKAPEZb7YnTMAdw0oCQDHk2DPrCbFR1MAaOh/EpSIlGg2dr+pJXDf79pcsOWd1Xqdvk5IoD/dKyhGMLx2FmCEu7xORppdj16tWa19ClIjzt3nzP9v/4/LOPP9cYHrABVnqhWQXDQylU7jfQXXYzZmU8sRyTnSbktEw0oxpwNpCPr2qepbKvf3mG43dptXEQBS1NUJ6F75htyoIhwi82enswWZKmK2qwZH343cv+/tJlRdsp16Wdsx1HWnnb7usXOUfkcyJXgFOEzMG2BIgIMtcnpKjWGg2Xjzm4/8Kzhgnebx6vNDzK58Rc0oQo2BTioc79EAxGOCF0y7tnUoVCshQuMmzrHAeIEK2ZMySKbUhIlD1koImWuNuFmG8DGeiDdS5rrC0LIgHeO6PPOr5w/d+sPOPQwuQ0NKTt2JaTswsFy7FkzkJxgOwSOSNkD8IuAgwJ4eShNXl1QEBQpapzljzn1OFTj3Iefrry/LZGX14Y3XnsCQ5QW28QsYYSkWZszPQE8fe+5t8JI78A3yB53pCQ6iaRADCP+K/JwpaQ5fNDvNmiZnVOkFI0U1VXnz9wzVWjRUvM1GA7liWkgBAClmPbff2iWCS7RPYyEitJjJFwSAoSCqoOrYhArIlYCNbM5VnvwBXOJWcNTJRr922sOJaUwifuQhxDap/giCiyBb8G5AdHQPaG1MnqgUTo9HaDBBsXG2RfaTkhbiMMC5KjWFz0VAB4+DqtNKFgj6yoPbhDxJ1xh5+Rgmp1tmx88B3Df3x2f3kWimBbkEJIKYVlCcuyHGHlIQolyo2QGGM1olWOyYLQxBWtPO0prRQxM+smOkhA1+rKEuLCMwZWjuHnvy03PORtzLWa/FB/oWcE2qO37vlJmOEDfMiNTcnY448VIoKChU2SBUTI0QeWCSNCOw67bKRPEyOCbmQRJWZoSJ1GDphUTuYXRApUajxcwqeuHn3VkYXxGW1bQkoAEBJCAEIIS0pHypwtnIK2+jUPSXtA9BdFsQABwBWOkjlluY1a1SXSxIpYEWsB1qwrs+rUQ/MnH+bc8Uh5zxQVc9AcUKxD4PgT+fANBWLAYRTVwo/2H8ltCeaqCabSNOgCdXFkYRCtyAbOoJTGmSE+u3SaUlJgh1Kzm1P2BUAamCNIGxd/LwWXa7xumbjmysEDlsmdE14hL5iImYmZtW5qH2nleXWSjSI1hF3yqJ92bp6+77cbH3rkuRde3FGpVAb65ZEbiq86pXjc/lZl0vWYwAxigKQgsmjvpDr90Px3/331H39090NPuyMl4Xo62WK20vGgbWy7TZw7iIkbRscKUw94C5EJyWCsSczI8jcHTM6xCb8SktKQcFqKkqxQlyFN7oBl8VkKKalcpXVj+qNXDqwYztVcyuekbQlLQliwLCEtYdm2ZVt2Liec/v6BvDOc/91z9he/N33nPTu2bRmvVhqWJYaHco5leQ1p5emiN4y898ph0XBdT7F2teey8pTnaq9er7tFR8/U3T+9dvKO39VGBoTnsc8pCpih7xD83JGyAc7GLF3JEBIUg24f/uEfQlqSWIhvY1TtEMCTGpiQIimEjo2TK8RcIiQ46xCatkZzLEpB5RqtHcMH39o/OuDUPHJsIUQzlJufNm3+CJvglBz3+V0z7/vCnn+89vn7frNtZqq6/5q+i89fe+Xl69eswZ5xl2DbFu64f2rbVPWNZ+YaNUWsWSvSilgxawGqN7yCJS46s++JzY3HnnP7CkIvclEFtWQ5vkjS3K5IVquKbUUG32HaiYmPcQkwpHlsSqQhhbOgoLsslRlbmxlJgGFWGphUpz/OwtQ8hOBqnVaO4AN/1Les5LhMOVsKIaSAkAIgiKYNkWLh2HCs6n/eOvPHn5y+++FGo6FWLSv83dVrP/nBw888fcU3/mfLT366Z3ZWELHSPFCy7nukum4/feJBTqXqEStmxewRaWINkKdIsr7orP5HX2hsfN7tK0jN3egMmKl/ISRgQ6aUxIY7JhH5GrA41Rs7WArPkaINKUTvqf1vkHDTcZwSXBYyYYm6TDEHmJiIWIDqHpUKuOaK0n4jdk2RY0MKCJCQECCgSYAKT4vhfuyc1ldfX/3cDxtCStVonHb82I3/ecoFb97v2Sfwpivu/82Dk/mcBQHNpJkUs/J4vKIvPivv1lxij7XbrIkzawYLUENpz/Vef3LxkRfU05vdYn6u9oB4fTVQcl2/xKPlYR4Xcejc0M6KFZgPGfEQBrYQRDgzY5cWQ8j0Zuscf2eZJtqKEnPIIBuimfk6PjIavmECuYpA/N5L+vYftWYbZMnm2jEvDLYyKyZP0ViJf/yod84Harc9qPsH5ezM7FmnLL/166867PCx5zfire++e+9kbXQ0p5m0Zs2smF1Fli2e3uJt31O30dDKZT1XDQeayhYsBNcaDE3XXT106Fo5PauliEKFxj+103BCx2IQQlc5HqYvhjk1CGXFIsShA3lstIg+DThkQnyd7YwTekjTCSKl+S/f2HfcAc5EWQsQCMy8MEfEmhUTKx7q05/4aeMdn6qNT6tcThet+gFrB2/8z1cWpWDP/tB/Prl5e6XQZ9dcpZoHEbPHrJgZNFunmXIDpFgr1opIN39BMIGYIYUoV1XR1p/68+EVQ6LhxWWL5g52OO4Rr7Fp8oM4UjfI1vgRy5Di7n42zWayuGQ23tsmYbdPBMuBHFUcBrrruE8hMFvn49Y7Zx9TmKhoy4LW80NyTEpprbWnSbDO2frvbnA/fJMeKLJb815/orVmed/73nPi6CpHa7Fta/2WX73Y3+/M1pWn2NPsMbmaPaamLWlm1i5rD8QEzayJNIEh5ibEmFkKTM3ygcvtv/mD4XqDRfMi4mWyixRRSEQ8GEz6nTJjjvHwWyOsYDBzQj8vMrkNToxgC6nCYam1AjmTRlVLTcyxhOcxNQfDGUoxcxOrxnVXWUK7LP70S/qGO/TIgJqdVSduwIXH27sbA289Z0ztrYkCNm+bnpqps4Cr2WV2Wbtae8yeZo+4pjiX14N5xZqkJIAE5ra7Vlop1nph93N5VuUdIUQc8lXjjRa/6Y0l1oTkrlgSsfsrMDiRfCi/zFm0zYdVQ+svyapqCDv5Wgo14S8k4yKgKQM2ms1WYmbSips/RKQ1Nzx2BE/OeO/8gnfHRhoqwdOsmK75I3nPY95B+xfyQ1KzIuUtH8k7OVHXusHc/OUyN5hcIk2oNPigNVg5BMWaSEvBAAuAtfY8rRQrxcpjZmrWvusN5T8wwTHWPStBMsSMMQ1xNAiGCKaxZgTpmXcSRHKQd4ns3GchA5Ph4d5iKMHI/0VyQ1Aw2yhSZ+HzoAWttVJaK1aaPY2c4PEpdfWX1SPP8kCRNFO5Jk47wjnlgNyDW/RwSbBgCFY1d/0hA6eftGZv2SUpGppdpgaTy+xq9kB1D+edlnOgNWtirVl7Hnue8jzyFHue1qw1g5mVIk9x+1h6eFvfP6LlwJgaoTSUvPCrvZSVNvFln9Y94vAkdSkGIKHagzBBjsNsP/ESiGxkHUzTYlchKvJM1LmQkoCmLZFmbrjaIjVRwXtusp7aIvYbI0sSMWlFrz9KsKuZ9fPby6iquSCNa//yl4cXcmK27goBpVk1yxXg8qxav5bfdKqamFYCxMyeq92G57lKKa01ex4rr0k5RHN4aM5YCgWLkiVxOZ+NRpHjH1mgxP1LJESPhoV2wbut7aSCj25F7IcToyKBNI1zToVLR5JQh7k5S05EpLX2lAbpqbL+62+LpzfzulXO+acskyCl2XZ4w3Jda3jrRrHx0cnnn5qAroOUmqmccEzua9ec6nm6UnNtC8QEYldxo+b929t0SbiuZtZKuYpYEWlWWnnac7VWpBSxJuURM7QirVtP3oxZ5NOHgb6dkjgBN3pQ9VootHA4P7oAwbClhmACdRgxg/g3oNhAzcPoufjHI9wq79HlDuf+BvPSHchm1nJukZjZU6oZwSjNShF7/K8/oidf0KvHxDknjuQcq6GImfIOBgvsaf2qQ7U35f7L9S+A6mq2QqTd8emLzhn7yefP2n9V3/jeOsCWBWj3uj+rXXaq13DZkqjXleupZnVB67nUSCluBpNak+uyUhzWt0vE2h1PLdcndm6bxzHYFdybACVWG8R/G8u+/hVES0Alb45A6XIeseIrJEFQ+qFgELWLEDJjBpCraM2IePkh0lVEgGIxkMPHbhd3bMSqZfKVx4z0F0TD442bqopJM7/lNBrI0bph75Zn5K/u2Ts26Jx+nO1N1aWQqkoHrS9cds5qpcUDj+2dmvKGSkzEW8btkSG7lPP6HcVaV2uqWiPXY9akNSmPNJPySHnkKbYkvbBT/eLRmmMt0LEitIDVjSSgzMBBSD4f3pH6IgOkEie/BnQbEu8DKwputHX5SyRVEk+IgvFFLoXFCGh/uq7Ha0bkyw+zXUWeoqE8fetBecN9cnTIPuXQ4UIOliAQP/piDaBKDWdsUAetIMfiDcv1Dx7Cj++ZGBsqnH5CiWcbJKR2qc/2XveasXNPXz5daTz4+NTGJ8XPnrBuvNv9+WO8YwqlPj1W0kULytPVOrkeE2vW0B5pJtdjSfTCLv3LjQuG1D2YhMglQjwrQhQSFgmUShDB8JTqlGo5IQOHnvymzUkWe38i9baCkIAkhiPYM5jMmNdDnDnIVbR6WL7iMHu2wQMFPPCi+OjPrP6COPqgkf68ZFZ5BwA9tqmqmV1PklAXHutN1Kxj19HoIP/sMfnjO/dOzdqvPrng5KAaREKoml69Sl7yurGzjh/bOl59cVO54Ymt4/YvH8IN9+LOx8XeqhzOe8M517Go4VG9TrpZsvNYMF7cpe98vGFbbZLsXRmuzxaCn1QMoh1bcHsJhmseaSrMYVOxvj69dRaAwyf9uirpgYxn86BV7qGRzNt3dHkHPW3OhYaIiEZywvySm6HdqhH58sNsIpqo4H03y4arDls3MtjnMGnborwtiLDxxVmlKWfTU9vplEP5yFW0tyzO2EDHrnN//TzdduveWx6dPeGwZWsPKIhaRTOYpa5569fKy89beej6wYceL+/eUxkalKzp+Z1058Pixt/aD2+Bp2n1IJccXWtQ3SPWZAnxwm591+M120KXIaGLMATo7BCgozsX+yxC9/AqYj1RhI7fofPbF0AM4Hjfgq5co7tZ4pMjLV8SBS906735np7oXYs7FF0OU+S6EYVs05BWj8gzDs0TiY/eJp7azgevGRgZKDJrKWFbsCUU05Obq5pJgjyPH3yRzzsJQzneW8FhK/i847yKlLfeW73+e1s0OScfM1LoJypXWQjtEit99FHFy163slzDnQ+OWxYVHLF6lPMWHntG3f6o+OXTQhMdOKoLQlfrZAv5wm6+6/GqY6HLfaOLxN8XKRljWpOTU/+E2kdw9QnmGkDZI9lJ9vUtpx4kRTAdMUHAfEtv0EAInIdBrJlBjkjQm4a0fECec0zumw/IHz6EdSuLI0MlgKWEFLAEWZKU4qe2VbUmEDk27xjHb17Qrz1aDeWwa0aU8uKNx/NpR9CWSe/r39n5lV9NrVlWOvqgoiClXE1CemW3T3hvfM3ohrV9P757b8MlCHHGBvuUw0o1xS/sxl1POPe8aA3l3PUjylNi8wTf/UTNkeEnkr9b4d4oc8NwKjx8GCiC5SQt25zJDo/Ha8fx6OES4q78a0QpKb7CK7jwnVeJMq32+biOULru0f4jGCs5H/k5hvqd5aNDRCwFpBQCJAXZFpSi57bX5vQMmPI5emGnuP0JnLyB1y/j6Zqs1MQhK/AHJ/PJG+iJF8rXfX7zjx+pbFg/etChQ0LVtQcm6Vbc4w9zzjxy8Pt37J2Z9Z7ZqQ5e3Xfq4cOjJYuYn97u3f64VXbptAP11nF1xxOuY2GeawIhDwqEDB12cOkTcSNo9DITN1GX8RXpkH2l5dleFPwS2Jj5i1kXzrdGnSxeROTgJ/yRTQE7ESBP0/J+3L+1sHNGrFkxIoQQ1JzngwCEIClIaX5+R00zASCQZhQd3jmJ7z3AA4N06kGiPy9mXWFJHLZKXXo6HXaw/On9k9d+fdumPXzisauHVxZ03ZO5fKPiHbSOTjp85Ju37ZagjZtnVw45K4YLY0OFgoOZSvWhZzBRp7X9tTufZMda2AgwOZE4PobNfEwZiXqtRuA0poDGSphdIymKQvb1LzdfH8P2cHz4J3wbAjBMeBCD3QEBrwx+osGAQ4SJItmSxmvO1rKzbGQgl8+DWQgSAgCkICFIgJhp066q1tTkIgaImXI2PCVu+Z14eDOOOICOXW/bjmiQdBlHrtZvf4UcG+CPfWvnF76/c9VI4YRTVwgA0nYbtGGDFJpvuWs8l7PHZ9x1ywqVGhfyTqnPqbnuQy+q7RPsekrNEzfAKGNcUJXlmHRQMIP4B5cl0GU3oCS0VHE4EGEajnVadrOP1AMEGyWUIeo4B0Bh2gOIS50RpvQWyZPWznzmR0XfCo8AyNPCLpb6+ktEWgAQwJyUGEvBUoCZN++uak3Nf2rOnjORFCjkxBPb5E338+5ZnLwBK4agyPZYaM0v30AXniJ+8Zj3+a9ueWpb9exX7FfIaxI2V/UpRxR+fP/UznG3WtfFnCgVnemyq1n29xca9fquiboNHUy9231vnCaiaydIaCswwZBxCwY6Paak8CYYGSCuFc1f4XxDdikKdxmPSsb+GIQcV+bT/6AorZfFYFHadmmFEBA0R88wTxhEAFkgZt68eyG0ay2xgpkKOYDFnY/wjx9SG9bx0QeSUtJyZJ2t1SM47wS+e5O47eat9z6x903n7e9Y5GmZH4I7q2/+1UQhL+ouLxsqzNa52tCuR7aTc2sVqMZcHBmHFxz7ZjLZoETKJlSrgBk5DwzQehTcR1rxkjEhNuJiTXboITAkjOtuEWyjbQ0SZth5yo+CFUTzyJkzEzF31LJm2jZe07yQsGAe5Lp4dX0F7Jygr/+SydJnH28RW5YDD3bR1iftV//JU/bGRyZe2NF40wXrtaeFFDnmL/9kpwRcj4cH865GzaWGqz2WRPBq0wAMphN7Z0W9NEBEB5khLU3E3V7YB32kxPJGTFlBFOHLRo1EVolIQwIxiRznhkB6jr9unnkLIAmypCBgx94qM4SAkKJJ09UsRzTfAYLW5FhkW/LW++TmGe+i08h1LSn0zCyPFUi7jbu39D/y6J61qwZOPmU56l7D1V/+wbaGqzRTqS8HyJqrPc1Kk/I8rzoFwDgEwkvLkOIyTIV6yTDUQvxys/USCep6QqkRrQ3IMagi0cE1AA4TRph7SJpIMzxNAEFzk+gb4KrrTVQa0+VGraFdj7Umrbld0koIQZYlbEvAEpbA6Cj++4fIy9q1b2tMNXJu3Z2p8tnHOJ+/m3cq65rPb7z03LV9/Tlt9SkmgJh5ZtYt9dlKsdakGE0gOsej48K+nK+AH9VUkLp8HCuKKKpzbEY+66VgQbxPvxpJjRMGG4+ZNKAZmgSBPa1mJqt7pyqz5QZpprw9MujsP1oYHcoPlWi0ZBXzttJc96hcbeyZdHeMu3v2NqZmXFXXZInCgPzMzbmT186cd4yamIZ2eaiA/UfUrhnr6efLt/5q2x9cum7LHq886xUcuB43XOUpbnIPaWbN5gCUXqz2Yg0Dcc0pvKLAtK+Qni0n0r40IVA2RLKmRP7dxSIsAh/RUurNiKwAxE2RWEG1Wm3nxHSjUrUK4qADBk4+evVpRw0ee0Bx7Yi1YjiXL0qyNC3MN7Agpcnj6brePek9t9v79ePlX/5mzwOPTVRnvb/+Zv+xaxorimrLXlFXLJsHq1Y/vW/PxZetv+P+LY2q15/PeaS0JqVJN39xk0NiHwYcTIt3GG0C6FALW+pTMx5nmbWvVzasMMPpYzqEnONofUy8uPmRjX8ABIQUXJmenJ0sW3k++ejBC1554DmnjR27oUBDTLpBM3WqNNy62ruLq40GsyYmR2KgKPM5SQ4N5HhgOQ5a6bz2uNH3vnno2a2ztz1c/uZtExd8bPyiE7wLjtMHDuhqHYK0FvT8ljJq9o9+tUNaxJpBpJk9xZqZm1oXEJFMTuhtIGekOYteCdP2oDA2v8+sfZgORYBIiY2WOeD8RxgtBndDFpDpIwMghZiamZ3d8+wBB/S97c2rr7xozYaDi+R51W3lh3478fvNtcc3N57cXHtxt9ozrabKbs3VTdvLOxgdtNaM2Yftlzv+QPuEg3NHHThsF5jq3kFj8qDzhq8+d+SOR1b+1w92/8W3Jl++emp3GXlbVGrsOOL+e/f++ne7+/ucJg0lIJpnUZM2kvaFWw8ai0aYfHry8A1Z6AElEQzslnXhJVxThOWMHFQRZ2PLMoNaZiwRDKDe8LTmk05Y/a7LD7nw9AK5jd9snL31vsm7Hp1+fFNt9zRTAySE7Yj+vCjlqD9PtmQi7SmenNW7Z6hRtahBJLU1jOM39J9/+vCFpxWPWV8gQVRWZDP12U+8wB+5YdfNd+zetbtGbv38cw8H4Ye3Pj44UFBMzDw0UHJyOVdppVmx9OoVTG0iyPY8D0tkSOwTFXB0AYDjkPBiqfZy1xcvW3mU79GL3hcS0nBtc/TqGyL/s7QiAEJAa71m9fBF5x+3//6Fhzdu/elduzc+XaNpjySoXw4MiJGSWFayhoqiPy8Gi7KUF/0OlXK6lFOlnOcIt+G5e2bomR3uw1to4w5rei9IIz9qn3Vc8bLXDl98al9/v6QKkRQ07OzY6X3hJ+Of/972rXs8t677CsIWpJlZ89DQoJCWp7lpSLpewcyWuTIvL+LeDZ84R0pBhryL/b1mVCUtBks5UjN7dVhALGq8XhkSm9KzI4h+JxKmyBmsY0a3CyImpdj1lOvqXCF3xOH71T3asXtypJ83rLYPXmkdOEpjJerPy4LtSnIlCMTMgoStWTQauuHB9WRDQTFbUuUtXbRc1t7uKb7/BfzqmfzvtkBPe+TQEYcW3nHOyB+eNbzfSodqIBJUFBOT/J07997wy8l7HpqanXaFg0JO9PcVHCevIZQmRVI3ZuX0Zp7T3pof4MOc5F54KYKDeR5j7QREtw5BnaOsS2ZIHLsTHWxITHFp1hMZEiImhGJApDiWZmgPfpRmKTFQyi1bVtpv1dDYiOjL1YdL6JOeW6lVK26lpqZm3MmKqjbmiBqZSIBsSX15a6AgRku8eoRWDWLZoCj1WULIel2XZ9lVyAnO28pz1aOb9fcf4XtezE9POeSpsTX2288duvq8sQ37FammqK6oYJNwfvui+51f7fn5fbs2Plctz2gith2Zy9nSzkvy7NrOpiCGZlZqjrYSINu2pCWCYogo+hoYBiaIQbERQOfAEZDwdJTIbDyUFWVIWcU6HE14EiuuQ7CupOFn9uxEAsZG+tatHerrc5SimZnq1OTM9Ex9asYtV3XDozlJIkFyEcU5L/c7J+4CIgiBnIOBPqwawcErxTFrrUNXylVDcCSU1qy0BU3c2LxX3vaU/fMnrce3C6qguMw+98yhy18z/KrDcqW+JgBJkpRuQzy+3f3Nk7O/e2pm47PTW7eXZ8purVL3GjViEuCcI/qK9uBQf6lUEBDj4zO7ds+05JWxePGB9ueOUPfHiYhoON7wbOwEye/khFEa0JS46o0hMZsDOKJtCaECreb22XF/HDT7Gcu8IGBJ4XqqVnM9TwGQUlqWtCSE6JaCXhBx7ppiBDST0tTw2PWYgFJBrB0T60axZphWDtJQkUt5HuunobyerdPvt+u7n3Puet7ZPpEjO3fgutzZxxXOPrF00sF9awZFbsChPptyFkmbPOJZt1zlybKueo5CbrampmYb4xONZ1+sPP7E+FNP7di6bW+t4bZmNDELmED7uzrKpJx2zJs5dpkhiRYDJwsUg6p2HfMn7I9eD2+5MEep5MbqhQeZevxMqc2QOEp+FAawO9YMkBBzdsIB6UaQrnPrgB2IAG7W0pRCXVETmiBAtmTHIsdiS1DBocE85aS3e5r21gsMe7JhuS7IsgZG8oesdY46aODg/fJrxnKjRTFQygkp67XG+LQ7PuW9uH326efGn980sWtXeWq6pjXZtmXblhBoMSQ2EGmNaArBTBbYXDyITQ8xTiNqEtuWEK1qzpGi0EhSEGNjIaToGkOaYiCnoJlEfMi/EaNpG20UN6cvmn+teZ5DnJiZlAYzORbZkputViGgWDQ8VF1qeNAEIckCW9CsWSmllGatALIt4TjSsYWUAjQPemgL6qKFmQ3SYMQ5TMIjMeYYm5A7+TgS1ZlN+YeJEAoRYjYqQ3PobCmTKXaKKXC0O5ZyTNgDMY5aOfLJclQDHrFI9jpLsPP3O3e4LXSNIQXLVpgyE5NgIs0ERUTalpyz5mTS53Iw3QwqJWA1BwebZ2ZTKSNO8NXaVWDjJ94c/I3Ok3kOg5dsPqZTeBSLy2iCVuEFLZ5karhWQvC06dZF2s/ODsjHXfscIdunA8OETPV2WmfOJISA8uZEIwIiDG7zbtyO/mj/0Yzuu2q+DUEOmtn82XA4009gBsVLQ8YfzzEE7hlkCFqN2mqdKx+cs5g4uECJ2jbcHEeN/y6iI+c/vKMT2DXKzmyQnYIg5GLpgOfEUsxzAf/P9JRqzDYajUahkM/lHGYSQhCINBFIL6hHYD7Ew/wpxRwkq4OI7c7txsfxJy05nLeQY3g4hAIXjBaUQ1n24zRjQElLfzBAfyPSluafjE8SH8WYgW44T9e/cSx/gtazxGwAHR0L3fVOKWWtVq/Mzi78a7GvkM/leAE13uZ5KMqhz60KM4+NDq9bt+bsV595z70P/vz2O/v7+yqVWU+pZoe0WCg0rRcEt+HWavXmlJFlW4V8nuc5tZJ6b452jqBY4w0I61S02QzMryGqh4uwS+KlmYrn3oxRZBO2cRTELtlKcEj1wO8RAJiYmFy/fv+zXnH62NioUmpiYvLe+367adNmx3HmRbzQhbaNEn4EXM87+qjDPnnd+1evXvG//+79P7nldgAnn3xssVhUStu2fOSRx8vlWSmF63qrVi0/ZMP6yuys4zgTeyeffOpZaVlLPhYBEz/NoUDkiIJs6l0FP6e8BPg70YPkxBDW0Xp4MIVyK3NoFSn477pbbAxDTQw0m6SiXCn/zV+/6yc3f23t2jWPP/HUs8+9cNqpJ95/z83vfMdlU1MzUspkXoyZ83nnO9/54Ze/cqPnqWq1JqX0PM9xct/42qd/8qOvveLlL5uaLluWJMCyrYnJqcsuu+S2W2/49Kc+2HBVqwn5alUF8pEt8sLDVIaRTcnQOKqcw10vjowsDewHfp/k99nB38eJdSTnb0OkP+qQUM2So0YfjVmkOUShzQg91W1GzYhuanr6ire/5YMfeO81H/3MP733X2699fabb/7pVVe9+1/f//ELzn8dsKA6NSfNN8fJ0A1lbf/LJnkDMdm5HGu2LAkQs3Yc+447733iyWeZ+fs/uLVWqzV1My0pd+/e8/0f3MLM99z7wIMP/C6XyzUF0pvZk0AHo/ocZ1EbC1bLdaB5DUL4Xu1iWggEtCszjZM40lwNY9TQoJ57q5puhZu8L+IQfuYfdDV+mBEypJHM4hBGzHi0xWWydmz7qisu9Tx1+y/uHluxxrEspfXgYOn/fvqLju2sXLl8enpGSikgCFSr1j2lbNvO53Os9XxlGZ7nMZNty4WyhucqzVzI51jr5qzdwjoXCnkhBIC+voKYz0+Z2bbsUn8/gJxj54sFZhaAkNJtuI1GA0Lkco4U0vM8pbUQEkRKaynmJiaU0lIKrbUU0rKk1rparWmtc/mcY9uep4i4WedwXVcKaUnpep7naSmFlFIpNe/xFqGYnMlQE4c/cbQyAsB/g3Vm1IlNgpNPdrII0WlnI0kBw0YkB5y/MXjLKJUAaJuqtolDYiLLspuu/FWvPGPPzt2ep4QQzJTPOdd/8eu1eh2AkGKmXC7PVNavX3fi8cesWLFsYmKqVmsIIQBSyhseHlq+fEwpPVeUIxocLK1auXzO1LDAYoCm1OxC2CalbO5jackmx1DzyGAmAJ6nxscnSqW+Y449YsPBByhPTU9N27ZV6u8DYFnW8ODgwmqOjg47jjM8NOg49tTUdL1RP+KIQ0468dhioTAxMSkEIES1WquUK4ODAwB2794rpRweGoAQ09Mz/pO1xmqXYerpFALTaXtHVNBoEivGkotOlyO1yq2GNFc4Jr9xy1vYJO1HdgkhB3sHbrlfn4KmEJXZyq9/8zspxQf+4x/+/h/fAyHGxydc17Ntx6033IYnpZycmDrr5afdeMPnrrryraeddtxHPvS+b3z10+vWrZmanl42NvLpT33gvntufs//+uPpmTJAuVzuo9f8y/33/uif/+lvypVZKYUUsjsSJKLp6ZmZqb3je6fG907u3Ts1OzNZLs8SkVYaxEqpfCH30Wved82H//kNr3vltR//9zt++d3zznv9zPT01Vdfee9dP/zZbTe98lVn1Gt1KUW90TjzzFPu+OV3r7ziLTt3bjvnDa++6Ybrzz3nNa997Vnf+5///uu/unq2WvNc9+KL3vDjm7/+i59959RTTvjn9/3V/3z7C3ff9cP77/3RO97xttlKdc6MI7J4nw2NpPzaQeE3fAvybLwdezIe4D9qzulDSfhNjHcNGHOvBx/MGovsC41XWvf39X38E5894fijX/aykz70gf/zR5dd8tWv3vSd7/xo05Ztw0ODQoiJyak/fMuFX/7Sdf/6b5/4t/d/zHHs//7SjT+/7du3/uQb55z71sce23j7L+669NKLhBSs2bbtnTt3/vBHt7797W8SQvB82LawueYZV0FE5577mvUHrssX8lozgHK5csqpxxOREBBCTExOfuW/P3XuuWcfecwrx/eMX3/912+95Vtf/9qnTznt9Z+49r8uv+yS9evX/X7j40p7zRu8597fbN++68Mf+eQ555797Zuu/7u/f/+1132OST/9zLP//YVra7XaZ/7rS/fc9+Df/u27999/zSWXnPeTW37+3R/csmb1mus/e82nrnv/73//5K9//du+vj6tdSD0Mkak1xJHczIOfQ7LK5CQ6itN9iBCFaZi61RHOgi/N/l6MUS4ro53xIQrd7188eNaEMts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"
        logo_data_uri = f"data:image/png;base64,{logo_base64}"
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{APP_NAME}</title>
        </head>
        <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f5f5f5;">
            <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f5f5f5; padding: 40px 20px;">
                <tr>
                    <td align="center">
                        <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                            <!-- Header -->
                            <tr>
                                <td style="background-color: #15182d; padding: 20px 30px; text-align: center;">
                                    <img src="{logo_data_uri}" alt="SoulHaven" style="width: 280px; height: auto; margin-bottom: 4px;">
                                    <p style="margin: 0; color: #d4af37; font-size: 14px; font-style: italic;">Seu companheiro de IA para apoio emocional e espiritual</p>
                                </td>
                            </tr>
                            <!-- Content -->
                            <tr>
                                <td style="padding: 40px 30px;">
                                    {content}
                                </td>
                            </tr>
                            <!-- Footer -->
                            <tr>
                                <td style="background-color: #f8f9fa; padding: 24px 30px; text-align: center; border-top: 1px solid #e9ecef;">
                                    <p style="margin: 0 0 8px 0; color: #6c757d; font-size: 12px;">
                                        Este email foi enviado por {APP_NAME}
                                    </p>
                                    <p style="margin: 0; color: #6c757d; font-size: 12px;">
                                        <a href="{APP_URL}" style="color: #d4af37; text-decoration: none;">soulhavenapp.com</a>
                                    </p>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """

    async def send_welcome_email(self, to: str, nome: str) -> bool:
        """Email de boas-vindas ao se registrar"""
        content = f"""
        <h2 style="margin: 0 0 20px 0; color: #1a1a2e; font-size: 24px;">Bem-vindo(a) ao SoulHaven, {nome}!</h2>

        <p style="margin: 0 0 16px 0; color: #4a4a4a; font-size: 16px; line-height: 1.6;">
            Que alegria ter voce conosco! O SoulHaven foi criado para ser seu companheiro
            espiritual, um lugar seguro para conversar, refletir e crescer na fe.
        </p>

        <p style="margin: 0 0 24px 0; color: #4a4a4a; font-size: 16px; line-height: 1.6;">
            Estou aqui para ouvir, acolher e caminhar com voce. Nao importa o que esteja
            enfrentando - ansiedade, duvidas, relacionamentos ou qualquer outra coisa -
            voce nao esta sozinho(a).
        </p>

        <div style="text-align: center; margin: 32px 0;">
            <a href="{APP_URL}" style="display: inline-block; background: linear-gradient(135deg, #d4af37 0%, #c9a227 100%); color: #1a1a2e; text-decoration: none; padding: 14px 32px; border-radius: 8px; font-weight: 600; font-size: 16px;">
                Comecar a Conversar
            </a>
        </div>

        <p style="margin: 24px 0 0 0; color: #6c757d; font-size: 14px; font-style: italic; text-align: center;">
            "Vinde a mim, todos os que estais cansados e sobrecarregados, e eu vos aliviarei." - Mateus 11:28
        </p>
        """

        return await self.send_email(
            to=to,
            subject=f"Bem-vindo(a) ao {APP_NAME}!",
            html=self._base_template(content)
        )

    async def send_password_reset_email(self, to: str, nome: str, reset_token: str) -> bool:
        """Email de recuperacao de senha"""
        reset_url = f"{APP_URL}?reset_token={reset_token}"

        content = f"""
        <h2 style="margin: 0 0 20px 0; color: #1a1a2e; font-size: 24px;">Recuperacao de Senha</h2>

        <p style="margin: 0 0 16px 0; color: #4a4a4a; font-size: 16px; line-height: 1.6;">
            Ola, {nome}!
        </p>

        <p style="margin: 0 0 16px 0; color: #4a4a4a; font-size: 16px; line-height: 1.6;">
            Recebemos uma solicitacao para redefinir sua senha. Se voce nao fez essa
            solicitacao, pode ignorar este email.
        </p>

        <p style="margin: 0 0 24px 0; color: #4a4a4a; font-size: 16px; line-height: 1.6;">
            Para criar uma nova senha, clique no botao abaixo:
        </p>

        <div style="text-align: center; margin: 32px 0;">
            <a href="{reset_url}" style="display: inline-block; background: linear-gradient(135deg, #d4af37 0%, #c9a227 100%); color: #1a1a2e; text-decoration: none; padding: 14px 32px; border-radius: 8px; font-weight: 600; font-size: 16px;">
                Redefinir Senha
            </a>
        </div>

        <p style="margin: 24px 0 0 0; color: #6c757d; font-size: 13px; text-align: center;">
            Este link expira em 1 hora. Se voce nao solicitou a recuperacao de senha,
            sua conta continua segura.
        </p>
        """

        return await self.send_email(
            to=to,
            subject=f"Recuperacao de Senha - {APP_NAME}",
            html=self._base_template(content)
        )

    async def send_subscription_confirmation(self, to: str, nome: str) -> bool:
        """Email de confirmacao de assinatura"""
        content = f"""
        <h2 style="margin: 0 0 20px 0; color: #1a1a2e; font-size: 24px;">Assinatura Confirmada!</h2>

        <p style="margin: 0 0 16px 0; color: #4a4a4a; font-size: 16px; line-height: 1.6;">
            Ola, {nome}!
        </p>

        <p style="margin: 0 0 16px 0; color: #4a4a4a; font-size: 16px; line-height: 1.6;">
            Obrigado por assinar o SoulHaven Premium! Sua assinatura foi confirmada
            e voce agora tem acesso ilimitado ao seu companheiro espiritual.
        </p>

        <div style="background-color: #f8f9fa; border-radius: 8px; padding: 20px; margin: 24px 0;">
            <h3 style="margin: 0 0 12px 0; color: #1a1a2e; font-size: 16px;">O que voce ganhou:</h3>
            <ul style="margin: 0; padding-left: 20px; color: #4a4a4a; font-size: 14px; line-height: 1.8;">
                <li>Mensagens ilimitadas</li>
                <li>Companheiro sempre disponivel</li>
            </ul>
        </div>

        <div style="text-align: center; margin: 32px 0;">
            <a href="{APP_URL}" style="display: inline-block; background: linear-gradient(135deg, #d4af37 0%, #c9a227 100%); color: #1a1a2e; text-decoration: none; padding: 14px 32px; border-radius: 8px; font-weight: 600; font-size: 16px;">
                Continuar Conversando
            </a>
        </div>

        <p style="margin: 24px 0 0 0; color: #6c757d; font-size: 14px; font-style: italic; text-align: center;">
            Que Deus abencoe sua jornada!
        </p>
        """

        return await self.send_email(
            to=to,
            subject=f"Assinatura Confirmada - {APP_NAME} Premium",
            html=self._base_template(content)
        )

    async def send_subscription_renewal(self, to: str, nome: str) -> bool:
        """Email de renovacao de assinatura"""
        content = f"""
        <h2 style="margin: 0 0 20px 0; color: #1a1a2e; font-size: 24px;">Assinatura Renovada!</h2>

        <p style="margin: 0 0 16px 0; color: #4a4a4a; font-size: 16px; line-height: 1.6;">
            Ola, {nome}!
        </p>

        <p style="margin: 0 0 16px 0; color: #4a4a4a; font-size: 16px; line-height: 1.6;">
            Sua assinatura do SoulHaven Premium foi renovada com sucesso.
            Continue aproveitando seu companheiro espiritual sem limites!
        </p>

        <div style="text-align: center; margin: 32px 0;">
            <a href="{APP_URL}" style="display: inline-block; background: linear-gradient(135deg, #d4af37 0%, #c9a227 100%); color: #1a1a2e; text-decoration: none; padding: 14px 32px; border-radius: 8px; font-weight: 600; font-size: 16px;">
                Ir para o SoulHaven
            </a>
        </div>

        <p style="margin: 24px 0 0 0; color: #6c757d; font-size: 14px; text-align: center;">
            Obrigado por continuar conosco!
        </p>
        """

        return await self.send_email(
            to=to,
            subject=f"Assinatura Renovada - {APP_NAME}",
            html=self._base_template(content)
        )

    async def send_subscription_expiring(self, to: str, nome: str, days_left: int) -> bool:
        """Email de aviso de vencimento proximo"""
        content = f"""
        <h2 style="margin: 0 0 20px 0; color: #1a1a2e; font-size: 24px;">Sua assinatura vence em breve</h2>

        <p style="margin: 0 0 16px 0; color: #4a4a4a; font-size: 16px; line-height: 1.6;">
            Ola, {nome}!
        </p>

        <p style="margin: 0 0 16px 0; color: #4a4a4a; font-size: 16px; line-height: 1.6;">
            Sua assinatura do SoulHaven Premium vence em <strong>{days_left} dias</strong>.
            Para continuar tendo acesso ilimitado ao seu companheiro espiritual,
            certifique-se de que seu metodo de pagamento esta atualizado.
        </p>

        <p style="margin: 0 0 24px 0; color: #4a4a4a; font-size: 16px; line-height: 1.6;">
            Se voce tem renovacao automatica ativada, nao precisa fazer nada -
            sua assinatura sera renovada automaticamente.
        </p>

        <div style="text-align: center; margin: 32px 0;">
            <a href="{APP_URL}" style="display: inline-block; background: linear-gradient(135deg, #d4af37 0%, #c9a227 100%); color: #1a1a2e; text-decoration: none; padding: 14px 32px; border-radius: 8px; font-weight: 600; font-size: 16px;">
                Verificar Assinatura
            </a>
        </div>
        """

        return await self.send_email(
            to=to,
            subject=f"Sua assinatura vence em {days_left} dias - {APP_NAME}",
            html=self._base_template(content)
        )

    async def send_subscription_cancelled(self, to: str, nome: str) -> bool:
        """Email de cancelamento de assinatura"""
        content = f"""
        <h2 style="margin: 0 0 20px 0; color: #1a1a2e; font-size: 24px;">Assinatura Cancelada</h2>

        <p style="margin: 0 0 16px 0; color: #4a4a4a; font-size: 16px; line-height: 1.6;">
            Ola, {nome}!
        </p>

        <p style="margin: 0 0 16px 0; color: #4a4a4a; font-size: 16px; line-height: 1.6;">
            Sua assinatura do SoulHaven Premium foi cancelada. Voce ainda pode usar
            o SoulHaven ate o final do periodo ja pago.
        </p>

        <p style="margin: 0 0 24px 0; color: #4a4a4a; font-size: 16px; line-height: 1.6;">
            Sentiremos sua falta! Se mudar de ideia, voce sempre pode voltar.
            Estaremos aqui esperando.
        </p>

        <div style="text-align: center; margin: 32px 0;">
            <a href="{APP_URL}" style="display: inline-block; background: linear-gradient(135deg, #d4af37 0%, #c9a227 100%); color: #1a1a2e; text-decoration: none; padding: 14px 32px; border-radius: 8px; font-weight: 600; font-size: 16px;">
                Reativar Assinatura
            </a>
        </div>

        <p style="margin: 24px 0 0 0; color: #6c757d; font-size: 14px; font-style: italic; text-align: center;">
            "Porque eu sei os planos que tenho para voces, diz o Senhor, planos de
            prosperidade e nao de calamidade, para dar-lhes um futuro e uma esperanca." - Jeremias 29:11
        </p>
        """

        return await self.send_email(
            to=to,
            subject=f"Assinatura Cancelada - {APP_NAME}",
            html=self._base_template(content)
        )


# Instancia global
email_service = EmailService()
