import AWS from 'aws-sdk';

// Initialize the Amazon Cognito credentials provider
const IDENTITY_POOL_ID = process.env.REACT_APP_IDENTITY_POOL_ID;
const REGION = process.env.REACT_APP_AWS_REGION;

AWS.config.region = REGION;
AWS.config.credentials = new AWS.CognitoIdentityCredentials({
    IdentityPoolId: IDENTITY_POOL_ID
});

// Initialize S3 with the credentials
const s3 = new AWS.S3({
    region: REGION,
    apiVersion: '2006-03-01',
    params: {
        Bucket: process.env.REACT_APP_S3_BUCKET
    },
    credentials: AWS.config.credentials
});

export const uploadFile = async (file) => {
  // Log initial attempt
  console.log('Starting upload process for file:', file.name);

  // Ensure credentials are loaded
  await new Promise((resolve, reject) => {
      AWS.config.credentials.get(err => {
          if (err) {
              console.error('Error loading credentials:', err);
              reject(err);
          } else {
              console.log('Credentials loaded successfully:', AWS.config.credentials);
              resolve();
          }
      });
  });

  const params = {
      Bucket: process.env.REACT_APP_S3_BUCKET,
      Key: `raw/${Date.now()}-${file.name}`,
      Body: file,
      ContentType: file.type
  };

  // Log upload parameters
  console.log('Upload params:', {
      Bucket: params.Bucket,
      Key: params.Key,
      ContentType: params.ContentType
  });

  try {
      console.log('Initiating S3 upload...');
      const response = await s3.upload(params).promise();
      console.log('Upload successful, response:', response);
      return response.Location;
  } catch (error) {
      console.error('Upload failed:', error);
      throw error;
  }
};



























