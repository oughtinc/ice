import { Box, Center, Flex, Icon } from "@chakra-ui/react";
import { FaGem } from "react-icons/fa";

export default function Nav() {
  return (
    <>
      <Center bg="blue.100" py={8}>
        {/* <Flex h={16} alignItems={'center'} justifyContent={'space-between'}> */}
        <Icon as={FaGem} w={8} h={8} color="blue.600" />
        {/* </Flex> */}
      </Center>
    </>
  );
}
