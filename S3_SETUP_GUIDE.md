# How to Configure Cloud Storage in LiveKit Console

To enable saving recordings, you **MUST** configure an S3-compatible bucket in the LiveKit Cloud Console.

### Step 1: Access the Console
1.  Log in to [LiveKit Cloud Console](https://cloud.livekit.io/).
2.  Select your project.
3.  Navigate to **Settings** (bottom left or dedicated tab).
4.  Find the **Egress** or **Recording** section.

### Step 2: Add Bucket Configuration
You need to provide your S3 details. If you have them in your `.env` file, they likely look like this:

*   **Endpoint**: (e.g., `s3.aws-region.amazonaws.com` or custom if using MinIO/GCP-interop)
*   **Bucket Name**: `your-bucket-name`
*   **Access Key**: `AKIA...`
*   **Secret Key**: `...`
*   **Region**: `us-east-1` (or your specific region)

**Instructions:**
1.  Click **"Add Egress Destination"** or **"Configure S3"**.
2.  Select **"S3"** (or GCP/Azure if applicable).
3.  Enter the values from your AWS/Cloud provider.
4.  **Save**.

### Step 3: Verify
Once saved, LiveKit will validate the bucket.
*   **Important**: LiveKit needs `PutObject` permission on that bucket to upload files.

### Why `.env` is not enough?
The `.env` file is for **your local Python agent** to talk to LiveKit.
However, **LiveKit's Servers** perform the actual recording and upload. Your local agent simply *requests* a recording. LiveKit's servers then need to know *where* to upload the file. That's why the credential must be in the Console, not just your local machine.
