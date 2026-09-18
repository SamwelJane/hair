import { useQuery } from "@tanstack/react-query";
import { apiClient } from "../../lib/apiClient";

export function useHomepageContent() {
  return useQuery({
    queryKey: ["homepage"],
    queryFn: async () => {
      const { data, error } = await apiClient.GET("/homepage", {});
      if (error) throw error;
      return data;
    },
    staleTime: 60_000,
  });
}
