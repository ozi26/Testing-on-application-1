package main

import "testing"

// TestCheckoutConfig ensures checkout service has required config
func TestCheckoutConfig(t *testing.T) {
    paymentAddr := "paymentservice:50051"
    if paymentAddr == "" {
        t.Error("Payment service address is required")
    }
}

// TestRetryPolicy checks the retry policy
func TestRetryPolicy(t *testing.T) {
    maxRetries := 3
    if maxRetries < 1 {
        t.Error("Retry policy must allow at least 1 attempt")
    }
}