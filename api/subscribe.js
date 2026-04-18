export default async function handler(req, res) {
  // Only allow POST
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const { email } = req.body;

  if (!email || !email.includes('@')) {
    return res.status(400).json({ error: 'A valid email is required' });
  }

  try {
    const response = await fetch(
      `https://api.convertkit.com/v3/forms/${process.env.CONVERTKIT_FORM_ID}/subscribe`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          api_key: process.env.CONVERTKIT_API_KEY,
          email: email.trim().toLowerCase(),
        }),
      }
    );

    const data = await response.json();

    if (!response.ok) {
      console.error('KIT error:', data);
      return res.status(400).json({ error: data.message || 'Subscription failed' });
    }

    return res.status(200).json({ success: true });

  } catch (error) {
    console.error('Server error:', error);
    return res.status(500).json({ error: 'Something went wrong. Please try again.' });
  }
}
