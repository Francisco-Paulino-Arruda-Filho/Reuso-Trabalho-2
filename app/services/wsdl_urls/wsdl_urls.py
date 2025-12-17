class WSDLProvider:
    WSDL_URLS = {
        "SP": "http://localhost:8080/?wsdl",
        "RJ": "http://localhost:8080/ws/NFeAutorizacao4.asmx?wsdl",
    }

    def get(self, uf: str) -> str:
        print("WSDLProvider.get called with uf:", uf)
        return self.WSDL_URLS.get(uf, "")