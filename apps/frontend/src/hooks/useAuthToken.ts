import { useAuth } from "@clerk/clerk-react";

export const useAuthToken = () => {
  const { getToken } = useAuth();

  const fetchToken = async () => {
    const token = await getToken();
    if (!token) {
      throw new Error("Missing auth token");
    }
    return token;
  };

  return { fetchToken };
};
