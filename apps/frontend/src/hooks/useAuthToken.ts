import { useAuth } from "@clerk/clerk-react";

export const useAuthToken = () => {
  const { getToken } = useAuth();

  const fetchToken = async () => {
    const template = import.meta.env.VITE_CLERK_JWT_TEMPLATE as string | undefined;
    const token = template ? await getToken({ template }) : await getToken();
    if (!token) {
      throw new Error("Missing auth token");
    }
    return token;
  };

  return { fetchToken };
};
