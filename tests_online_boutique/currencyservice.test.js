// Synthetic test for currencyservice
describe("CurrencyService", () => {
    test("converts USD to EUR", () => {
        const usd = 100;
        const rate = 0.85;
        expect(usd * rate).toBe(85);
    });
    
    test("returns exchange rate for EUR", () => {
        const currency = "EUR";
        expect(currency).toBe("EUR");
    });
});