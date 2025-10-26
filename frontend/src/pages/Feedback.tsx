import React, { useState } from "react";

export default function Feedback() {
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    subject: "",
    message: "",
    type: "general"
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitStatus, setSubmitStatus] = useState<"idle" | "success" | "error">("idle");

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setSubmitStatus("idle");

    try {
      // Create mailto link with form data
      const subject = encodeURIComponent(`[Ramblin Recs Feedback] ${formData.subject}`);
      const body = encodeURIComponent(`
Name: ${formData.name}
Email: ${formData.email}
Type: ${formData.type}

Message:
${formData.message}

---
Sent from Ramblin Recs Feedback Form
      `);
      
      const mailtoLink = `mailto:ramblinrecssupport@gmail.com?subject=${subject}&body=${body}`;
      
      // Open email client
      window.location.href = mailtoLink;
      
      // Simulate success after a short delay
      setTimeout(() => {
        setSubmitStatus("success");
        setIsSubmitting(false);
        setFormData({
          name: "",
          email: "",
          subject: "",
          message: "",
          type: "general"
        });
      }, 1000);
      
    } catch (error) {
      setSubmitStatus("error");
      setIsSubmitting(false);
    }
  };

  return (
    <div>
      <h2>Send Feedback</h2>
      <p>We'd love to hear from you! Send us your feedback, suggestions, or report any issues.</p>
      
      {submitStatus === "success" && (
        <div style={{ 
          padding: "12px", 
          backgroundColor: "#d4edda", 
          border: "1px solid #c3e6cb", 
          borderRadius: "4px", 
          color: "#155724",
          marginBottom: "16px"
        }}>
          ✅ Your email client should have opened with your feedback ready to send. Thank you for your feedback!
        </div>
      )}
      
      {submitStatus === "error" && (
        <div style={{ 
          padding: "12px", 
          backgroundColor: "#f8d7da", 
          border: "1px solid #f5c6cb", 
          borderRadius: "4px", 
          color: "#721c24",
          marginBottom: "16px"
        }}>
          ❌ There was an error. Please try again or email us directly at ramblinrecssupport@gmail.com
        </div>
      )}

      <form onSubmit={handleSubmit} style={{ maxWidth: "600px" }}>
        <div style={{ marginBottom: "16px" }}>
          <label htmlFor="name" style={{ display: "block", marginBottom: "4px", fontWeight: "bold" }}>
            Name *
          </label>
          <input
            type="text"
            id="name"
            name="name"
            value={formData.name}
            onChange={handleChange}
            required
            style={{
              width: "100%",
              padding: "8px",
              border: "1px solid #ccc",
              borderRadius: "4px",
              fontSize: "16px"
            }}
          />
        </div>

        <div style={{ marginBottom: "16px" }}>
          <label htmlFor="email" style={{ display: "block", marginBottom: "4px", fontWeight: "bold" }}>
            Email *
          </label>
          <input
            type="email"
            id="email"
            name="email"
            value={formData.email}
            onChange={handleChange}
            required
            style={{
              width: "100%",
              padding: "8px",
              border: "1px solid #ccc",
              borderRadius: "4px",
              fontSize: "16px"
            }}
          />
        </div>

        <div style={{ marginBottom: "16px" }}>
          <label htmlFor="type" style={{ display: "block", marginBottom: "4px", fontWeight: "bold" }}>
            Feedback Type
          </label>
          <select
            id="type"
            name="type"
            value={formData.type}
            onChange={handleChange}
            style={{
              width: "100%",
              padding: "8px",
              border: "1px solid #ccc",
              borderRadius: "4px",
              fontSize: "16px"
            }}
          >
            <option value="general">General Feedback</option>
            <option value="bug">Bug Report</option>
            <option value="feature">Feature Request</option>
            <option value="event">Event Suggestion</option>
            <option value="other">Other</option>
          </select>
        </div>

        <div style={{ marginBottom: "16px" }}>
          <label htmlFor="subject" style={{ display: "block", marginBottom: "4px", fontWeight: "bold" }}>
            Subject *
          </label>
          <input
            type="text"
            id="subject"
            name="subject"
            value={formData.subject}
            onChange={handleChange}
            required
            placeholder="Brief description of your feedback"
            style={{
              width: "100%",
              padding: "8px",
              border: "1px solid #ccc",
              borderRadius: "4px",
              fontSize: "16px"
            }}
          />
        </div>

        <div style={{ marginBottom: "16px" }}>
          <label htmlFor="message" style={{ display: "block", marginBottom: "4px", fontWeight: "bold" }}>
            Message *
          </label>
          <textarea
            id="message"
            name="message"
            value={formData.message}
            onChange={handleChange}
            required
            rows={6}
            placeholder="Please provide details about your feedback, suggestions, or any issues you've encountered..."
            style={{
              width: "100%",
              padding: "8px",
              border: "1px solid #ccc",
              borderRadius: "4px",
              fontSize: "16px",
              resize: "vertical"
            }}
          />
        </div>

        <button
          type="submit"
          disabled={isSubmitting}
          style={{
            backgroundColor: isSubmitting ? "#ccc" : "#007bff",
            color: "white",
            padding: "12px 24px",
            border: "none",
            borderRadius: "4px",
            fontSize: "16px",
            cursor: isSubmitting ? "not-allowed" : "pointer",
            fontWeight: "bold"
          }}
        >
          {isSubmitting ? "Opening Email..." : "Send Feedback"}
        </button>
      </form>

      <div style={{ marginTop: "24px", padding: "16px", backgroundColor: "#f8f9fa", borderRadius: "4px" }}>
        <h3>Alternative Contact Methods</h3>
        <p>
          <strong>Email:</strong> <a href="mailto:ramblinrecssupport@gmail.com">ramblinrecssupport@gmail.com</a>
        </p>
        <p>
          <strong>Response Time:</strong> We typically respond within 24-48 hours during business days.
        </p>
        <p>
          <strong>What to Include:</strong> Please include your device type, browser, and any error messages you see.
        </p>
      </div>
    </div>
  );
}


