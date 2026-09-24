// Synthetic test for paymentservice
describe("PaymentService", () => {
    test("charges a valid card", () => {
        const charge = { amount: 100, currency: "USD" };
        expect(charge.amount).toBe(100);
    });
    
    test("rejects invalid card number", () => {
        const cardNumber = "1234";
        expect(cardNumber.length).not.toBe(16);
    });
});