import { v2 as cloudinary } from "cloudinary";

cloudinary.config({
  cloud_name: process.env.CLOUDINARY_CLOUD_NAME,
  api_key: process.env.CLOUDINARY_API_KEY,
  api_secret: process.env.CLOUDINARY_API_SECRET,
});

export interface UploadResult {
  url: string;
  publicId: string;
}

export async function uploadImage(fileBuffer: Buffer, folder = "hiar-business/products"): Promise<UploadResult> {
  return new Promise((resolve, reject) => {
    const stream = cloudinary.uploader.upload_stream({ folder }, (error, result) => {
      if (error || !result) return reject(error ?? new Error("Cloudinary upload failed"));
      resolve({ url: result.secure_url, publicId: result.public_id });
    });
    stream.end(fileBuffer);
  });
}
